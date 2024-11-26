import logging

import pandas as pd
from pathlib import Path

from insitupy.io.metadata import MetaDataParser
from . import SnowExMetadataVariables, SnowExPrimaryVariables
from insitupy.variables import MeasurementDescription
from insitupy.profiles.base import ProfileData, standardize_depth


LOG = logging.getLogger(__name__)


class SnowExMetadataParser(MetaDataParser):
    METADATA_VARIABLE_CLASS = SnowExMetadataVariables
    PRIMARY_VARIABLES_CLASS = SnowExPrimaryVariables


class SnowExProfileData(ProfileData):
    META_PARSER = SnowExMetadataParser

    @classmethod
    def from_csv(
        cls, fname, variable: MeasurementDescription, timezone="US/Mountain",
        allow_map_failures=False
    ):
        """
        Args:
            fname: path to file
            variable: variable in the file
            timezone: local timezone for file
            allow_map_failures: allow metadata and column unknowns
        Returns:
            the instantiated class
        """
        meta_parser = cls.META_PARSER(
            fname, timezone, allow_map_failures=allow_map_failures
        )
        # Parse the metadata and column info
        metadata, columns, columns_map, header_pos = meta_parser.parse()
        # read in the actual data
        if columns is None and not columns_map:
            # Use an empty dataframe if the file is empty
            LOG.warning(f"File {fname} is empty of rows")
            data = pd.DataFrame()
        else:
            data = cls.read_csv_dataframe(fname, columns, header_pos)

        return cls(data, metadata, variable, meta_parser.units_map)

    @staticmethod
    def read_csv_dataframe(profile_filename, columns, header_position):
        """
        Read in a profile file. Managing the number of lines to skip and
        adjusting column names

        Args:
            profile_filename: Filename containing a manually measured
                             profile
            columns: list of columns to use in dataframe
            header_position: skiprows for pd.read_csv
        Returns:
            df: pd.dataframe contain csv data with desired column names
        """
        # header=0 because docs say to if using skip rows and columns
        df = pd.read_csv(
            profile_filename, header=0,
            skiprows=header_position,
            names=columns,
            encoding='latin'
        )
        # Special SMP specific tasks
        depth_fmt = 'snow_height'
        is_smp = False
        if 'force' in df.columns:
            # Convert depth from mm to cm
            df['depth'] = df['depth'].div(10)
            is_smp = True
            # Make the data negative from snow surface
            depth_fmt = 'surface_datum'

            # SMP serial number and original filename for provenance to the comment
            f = Path(profile_filename).name
            serial_no = f.split('SMP_')[-1][1:3]

            df['comments'] = f"fname = {f}, " \
                             f"serial no. = {serial_no}"

        if not df.empty:
            # Standardize all depth data
            new_depth = standardize_depth(
                df['depth'], desired_format=depth_fmt, is_smp=is_smp
            )

            if 'bottom_depth' in df.columns:
                delta = df['depth'] - new_depth
                df['bottom_depth'] = df['bottom_depth'] - delta

            df['depth'] = new_depth

            delta = abs(df['depth'].max() - df['depth'].min())
            LOG.debug(
                f'File contains a profile with'
                f' with {len(df)} layers across {delta:0.2f} cm'
            )
        if "flags" in df.columns:
            # Max length of the flags column
            df["flags"] = df["flags"].str.replace(" ", "")

        return df

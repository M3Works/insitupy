"""
Point data from select manual measurement campaigns
"""
import logging
from pathlib import Path
import geopandas as gpd
from typing import List

import numpy as np
import pandas as pd

from .metadata import MetaDataParser, ProfileMetaData
from .variables import ProfileVariables, MeasurementDescription, \
    SnowExProfileVariables

"""

# Start with this
https://github.com/SnowEx/snowex_db/blob/main/scripts/upload/add_time_series_pits.py
data from https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_TS_SP.001/2020.04.27/

# TODO: What do we need here

https://github.com/SnowEx/snowex_db/blob/main/scripts/upload/add_iop_pits.py
https://github.com/SnowEx/snowex_db/blob/main/scripts/upload/add_sbb_depths.py
https://github.com/SnowEx/snowex_db/blob/main/scripts/upload/add_snow_depths.py

SMP
    https://github.com/SnowEx/snowex_db/blob/main/scripts/upload/add_smp.py
    https://github.com/SnowEx/snowex_db/blob/main/scripts/upload/resample_smp.py

Maybe not
    https://github.com/SnowEx/snowex_db/blob/main/scripts/upload/add_snow_poles.py


"""

SOURCES = [
    "https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_SSA.001/",
    "https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_BSU_GPR.001/",
    "https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_GM_SP.001/",
    "https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_SMP.001/",
    "https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_SD.001/",
    ("https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_GM_CSU_GPR.001/2020.02.06/"
     "SNEX20_GM_CSU_GPR_1GHz_v01.csv"),
    ("https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_UNM_GPR.001/2020.01.28/"
     "SNEX20_UNM_GPR.csv"),
    ("https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_SD_TLI.001/2019.09.29/"
     "SNEX20_SD_TLI_clean.csv"),
]


"""
Start with pit density, temperature measurements

Big pluses
    * variable name mapping

# TODO
    * will need login info for NSIDC
    * stratigraphy will be the most complicated

# TODO Next
    * Clean up the metadata file reading
        * We don't need everything we're reading right now
    * map to sample_a, sample_b when reading in file
    * flush out density and swe calcs

"""

LOG = logging.getLogger(__name__)


class ProfileData:
    """
    This would be one pit, SMP profile, etc
    Unique date, location, variable
    """
    VARIABLES = ProfileVariables
    META_PARSER = MetaDataParser

    def __init__(
        self, input_df, metadata: ProfileMetaData, variable: MeasurementDescription,
    ):
        """
        Take df of layered data (SMP, pit, etc)
        Args:
            input_df: dataframe of data
                Should include depth and optional bottom depth
                Should include sample or sample_a, sample_b, etc

        """
        self._depth_layer = self.VARIABLES.DEPTH
        self._lower_depth_layer = self.VARIABLES.BOTTOM_DEPTH
        self._metadata = metadata
        # TODO: auto parse variable if not given
        self.variable: MeasurementDescription = variable
        # mapping of column name to measurement type
        self._column_mappings = {}
        # List of measurements to keep
        self._measurements_to_keep = [
            self._depth_layer, self._lower_depth_layer, self.variable
        ]

        self._id = metadata.id
        self._dt = metadata.date_time

        # This will populate the column mapping
        self._df = self._format_df(input_df)

        columns = self._df.columns.values
        if self._depth_layer.code not in columns:
            raise ValueError(f"Expected {self._depth_layer} in columns")

        # List of columns that are not the desired variable
        _non_measure_columns = [
            self._depth_layer.code, self._lower_depth_layer.code,
            "datetime",
            "geometry"
        ]
        self._non_measure_columns = [
            c for c in _non_measure_columns if c in columns
        ]

        # Columns related to the variable
        self._sample_columns = [
            c for c in columns if self._column_mappings.get(c) == self.variable
        ]
        if len(self._sample_columns) == 0:
            raise ValueError(f"No sample columns in {columns}")

        # describe the data a bit
        self._has_layers = self._lower_depth_layer.code in columns
        # More than 1 sample of the variable (sample_1, sample_2)...
        self._multi_sample = len(self._sample_columns) > 1
        # Extend the df info
        self._extend_df()

    def _format_df(self, input_df):
        """
        Format the incoming df with the column headers and other info we want
        """

        # Get rid of columns we don't want and populate column mapping
        columns = input_df.columns.values
        for c in columns:
            cn, cm = self.VARIABLES.from_mapping(c)
            # join with existing mappings
            self._column_mappings = {**cm, **self._column_mappings}

        columns_to_keep = [
            c for c in columns
            if self._column_mappings[c] in self._measurements_to_keep
        ]
        df = input_df.loc[:, columns_to_keep]

        n_entries = len(df)
        df["datetime"] = [self._dt] * n_entries

        # parse the location
        lat, lon = self.latlon
        location = gpd.points_from_xy(
            [lon] * n_entries, [lat] * n_entries
        )

        df = gpd.GeoDataFrame(
            df, geometry=location
        ).set_crs("EPSG:4326")
        df = df.replace(-9999, np.NaN)

        return df

    def _extend_df(self):
        # set the thickness of the layer
        if self._has_layers:
            self._df[self.VARIABLES.LAYER_THICKNESS.code] = (
                self._df[self._depth_layer.code] - self._df[
                    self._lower_depth_layer.code
                ]
            )

    @property
    def latlon(self):
        # return location metadata
        return self._metadata.latitude, self._metadata.longitude

    @property
    def df(self):
        return self._df

    @property
    def sum(self):
        # get bulk value
        if not self._has_layers:
            # could we assume equidistant spacing and do a mean?
            raise RuntimeError("Cannot compute for no layers")

        # this should work for multi or not multi sample
        profile_average = self._df.loc[:, self._sample_columns].mean(axis=1)
        self._df["mean"] = profile_average
        # TODO: sum up with depth change
        # TODO: could we use the weighted mean * the total depth?
        # TODO: units
        pass

    @property
    def mean(self):
        profile_average = self._df.loc[:, self._sample_columns].mean(
            axis=1)
        if pd.isna(profile_average).all():
            return np.nan
        if self._has_layers:
            # height weighted mean for these layers
            thickness = self._df[self.VARIABLES.LAYER_THICKNESS.code]
            # this works for a weighted mean, but is not assumed to be
            # the total thickness of the snowpack
            thickness_total = thickness.sum()
            weighted_mean = (
                profile_average * thickness / thickness_total
            ).sum()
            value = weighted_mean
        else:
            value = np.mean(profile_average)

        return value

    @property
    def total_depth(self):
        profile = self._df.loc[:, self._depth_layer.code].values
        return np.nanmax(profile)

    def get_profile(self, snow_datum="ground"):
        # TODO: snow datum is ground or snow
        # get profile of values
        profile_average = self._df.loc[:, self._sample_columns].mean(
            axis=1)
        df = self._df.copy()
        df[self.variable.code] = profile_average
        columns_of_interest = [*self._non_measure_columns, self.variable.code]
        return df.loc[:, columns_of_interest]

    @classmethod
    def from_file(self, fname, variable: ProfileVariables):
        raise NotImplementedError("Not implemented")


class SnowExMetadataParser(MetaDataParser):
    VARIABLES_CLASS = SnowExProfileVariables


class SnowExProfileData(ProfileData):
    VARIABLES = SnowExProfileVariables
    META_PARSER = SnowExMetadataParser

    @classmethod
    def from_file(cls, fname, variable: MeasurementDescription):
        # TODO: timezone here (mapped from site?)
        meta_parser = cls.META_PARSER(fname, "US/Mountain")
        # Parse the metadata and column info
        metadata, columns, header_pos = meta_parser.parse()
        # read in the actual data
        data = cls._read(fname, columns, header_pos)

        return cls(data, metadata, variable)

    @staticmethod
    def _read(profile_filename, columns, header_position):
        """
        # TODO: better name mapping here
        Read in a profile file. Managing the number of lines to skip and
        adjusting column names

        Args:
            profile_filename: Filename containing the a manually measured
                             profile
        Returns:
            df: pd.dataframe contain csv data with standardized column names
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
        return df


class ProfileDataCollection:
    """
    This could be a collection of pits, profiles, etc
    """

    def __init__(self, df):
        self._df = df
        pass

    @property
    def SWE(self):
        """
        Takes all layers for each unique date, location and returns point swe
        geodataframe
        We can iterate though all ProfileData in this class and get SWE DF for each
        """
        # find all points with variable == density and calc SWE
        pass

    def get_mean(self, variable: MeasurementDescription):
        raise NotImplementedError()

    def get_sum(self, variable: MeasurementDescription):
        raise NotImplementedError()

    def get_profile(self, variable: MeasurementDescription):
        raise NotImplementedError()

    # def get_pit_data(self, start_date, end_date, variables) -> List[PointData]:
    #     """
    #     Returns a geodataframe
    #     """
    #     pass

    @property
    def metadata(self):
        # might be a map of date to location
        pass

    @classmethod
    def points_from_geometry(
        cls,
        geometry: gpd.GeoDataFrame,
        variables: List[MeasurementDescription],
        snow_courses=False,
        within_geometry=True,
        buffer=0.0
    ):
        pass

    @classmethod
    def from_files(cls):
        # parse mlutiple files and create an iterable of ProfileData
        pass


def standardize_depth(depths, desired_format='snow_height', is_smp=False):
    """
    Data that is a function of depth comes in 2 formats. Sometimes 0 is
    the snow surface, sometimes 0 is the ground. This function standardizes it
    for each profile. desired_format can be:

        snow_height: Zero at the bottom of the data.
        surface_datum: Zero at the top of the data and uses negative depths
                       (easier for plotting)

    Args:
        depths: Pandas series of depths in either format
        desired_format: string indicating which format the data is in
        is_smp: Boolean indicating which data this is, if smp then the data is
                surface_datum but with positive depths
   Returns:
        new:
    """
    max_depth = depths.max()
    min_depth = depths.min()

    new = depths.copy()

    # How is the depth ordered
    # max_depth_at_top = depths.iloc[0] > depths.iloc[-1]

    # Is the data in surface_datum already
    bottom_is_negative = depths.iloc[-1] < 0

    if desired_format == 'snow_height':

        if is_smp:
            LOG.info('Converting SMP depths to snow height format.')
            new = (depths - max_depth).abs()

        elif bottom_is_negative:
            LOG.info('Converting depths in surface datum to snow height format.')

            new = (depths + abs(min_depth))

    elif desired_format == 'surface_datum':
        if is_smp:
            LOG.info('Converting SMP depths to surface datum format.')
            new = depths.mul(-1)

        elif not bottom_is_negative:
            LOG.info('Converting depths in snow height to surface datum format.')
            new = depths - max_depth

    else:
        raise ValueError(
            f'{desired_format} is an invalid depth format! Options are:'
            f' {["snow_height", "surface_datum"]}'
        )

    return new

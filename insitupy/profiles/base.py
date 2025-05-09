import logging

import geopandas as gpd
import numpy as np
import pandas as pd

from insitupy.io.metadata import MetaDataParser
from insitupy.variables import (ExtendableVariables, MeasurementDescription,
                                base_metadata_variables_yaml,
                                base_primary_variables_yaml)
from .metadata import ProfileMetaData

LOG = logging.getLogger(__name__)


class MeasurementData:
    """
    This would be one pit, SMP profile, etc
    Unique date, location, variable
    """
    DEFAULT_METADATA_VARIABLE_FILES = [
        base_metadata_variables_yaml
    ]
    DEFAULT_PRIMARY_VARIABLE_FILES = [
        base_primary_variables_yaml
    ]

    def __init__(
        self,
        input_df: pd.DataFrame,
        metadata: ProfileMetaData,
        variable: MeasurementDescription,
        meta_parser: MetaDataParser,
        original_file=None,
        allow_map_failure=False
    ):
        """
        Take df of layered data (SMP, pit, etc)
        Args:
            input_df: dataframe of data
                Should include depth and optional bottom depth
                Should include sample or sample_a, sample_b, etc
            metadata: ProfileMetaData object
            meta_parser: MetaDataParser object. This will hold our variables
                map and units map
            variable: description of variable
            original_file: optional track original file
            allow_map_failure: if a mapping fails, warn us and use the
                original string (default False)

        """
        self._meta_parser = meta_parser
        self._units_map = meta_parser.units_map
        self._original_file = original_file
        self._metadata = metadata
        self._allow_map_failure = allow_map_failure
        self.variable: MeasurementDescription = variable
        # mapping of column name to measurement type
        self._column_mappings = {}

        self._sample_column = None
        # This will populate the column mapping
        # and filter to the desired measurement column
        if input_df.empty:
            LOG.warning("DF is empty")
            self._df = input_df
        else:
            self._df = self._format_df(input_df)

    def _format_df(self, input_df):
        raise NotImplementedError("not implemented")

    def _set_column_mappings(self, input_df):
        # Get rid of columns we don't want and populate column mapping
        columns = input_df.columns.values
        for c in columns:
            # Find the variable associated with each column
            # and store a map
            cn, cm = self._meta_parser.primary_variables.from_mapping(
                c, allow_failure=self._allow_map_failure
            )
            # join with existing mappings
            self._column_mappings = {**cm, **self._column_mappings}

    def _check_sample_columns(self, input_df):
        columns = input_df.columns.values
        _sample_columns = [
            c for c in columns if self._column_mappings.get(c) == self.variable
        ]
        if len(_sample_columns) == 0:
            raise ValueError(
                f"No sample columns in {columns}. This is likely because"
                f" variable {self.variable} is not in columns"
                f" {input_df.columns}"
            )
        elif len(_sample_columns) > 1:
            LOG.warning(
                "Only one sample column allowed, keeping the first match"
            )
            _sample_columns = [_sample_columns[0]]
        _sample_column = _sample_columns[0]
        # Rename the variable column to the variable code
        # This covers the scenario where we did not auto-remap the
        # variable on original parsing of the column names because
        # it was a multi-sample variable
        # Columns related to the variable
        sample_column_type = self._column_mappings[_sample_column]
        if sample_column_type != self.variable:
            raise ValueError(
                f"{sample_column_type} and {self.variable} are not the same"
            )
        input_df.rename(
            columns={_sample_column: sample_column_type.code},
            inplace=True
        )
        self._sample_column = sample_column_type.code
        return input_df

    @property
    def metadata(self):
        return self._metadata

    @property
    def units_map(self):
        return self._units_map

    @property
    def latlon(self):
        # return location metadata
        return self._metadata.latitude, self._metadata.longitude

    @property
    def df(self):
        return self._df

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
        raise NotImplementedError("Not implemented")

    @classmethod
    def from_csv(
        cls,
        fname,
        variable: MeasurementDescription,
        timezone="US/Mountain",
        allow_map_failures=False,
        metadata_variable_files=None,
        primary_variable_files=None
    ):
        """
        Args:
            fname: path to file
            variable: variable in the file
            timezone: local timezone for file
            allow_map_failures: allow metadata and column unknowns
            metadata_variable_files: list of yaml files with metadata variables
            primary_variable_files: list of yaml files with primary variables
        Returns:
            the instantiated class
        """
        primary_variable_files = primary_variable_files or \
            cls.DEFAULT_PRIMARY_VARIABLE_FILES
        metadata_variable_files = metadata_variable_files or \
            cls.DEFAULT_METADATA_VARIABLE_FILES
        meta_parser = MetaDataParser(
            fname, timezone,
            ExtendableVariables(entries=primary_variable_files),
            ExtendableVariables(entries=metadata_variable_files),
            allow_map_failures=allow_map_failures
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

        return cls(data, metadata, variable, meta_parser)


class ProfileData(MeasurementData):
    """
    This would be one pit, SMP profile, etc
    Unique date, location, variable
    """
    def __init__(
        self,
        input_df: pd.DataFrame,
        metadata: ProfileMetaData,
        variable: MeasurementDescription,
        meta_parser: MetaDataParser,
        original_file=None,
        allow_map_failure=False
    ):
        """
        Take df of layered data (SMP, pit, etc)
        Args:
            input_df: dataframe of data
                Should include depth and optional bottom depth
                Should include sample or sample_a, sample_b, etc
            metadata: ProfileMetaData object
            meta_parser: MetaDataParser object. This will hold our variables
                map and units map
            variable: description of variable
            original_file: optional track original file
            allow_map_failure: if a mapping fails, warn us and use the
                original string (default False)

        """
        # These are our default shared columns
        self._depth_columns = [
            meta_parser.primary_variables.entries["DEPTH"],
            meta_parser.primary_variables.entries["BOTTOM_DEPTH"]
        ]
        self._depth_layer = self._depth_columns[0]
        self._lower_depth_layer = self._depth_columns[1]
        # List of measurements to keep
        self._measurements_to_keep = (
            self.shared_column_options() + [variable]
        )
        self._id = metadata.site_name
        self._dt = metadata.date_time
        # Init the measurement class
        super().__init__(
            input_df, metadata, variable,
            meta_parser,
            original_file=original_file,
            allow_map_failure=allow_map_failure
        )
        columns = self._df.columns.values
        if len(columns) > 0 and self._depth_layer.code not in columns:
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

        # describe the data a bit
        self._has_layers = self._lower_depth_layer.code in columns
        # Extend the df info
        self._add_thickness_to_df()

    def shared_column_options(self):
        return self._depth_columns

    def _format_df(self, input_df):
        """
        Format the incoming df with the column headers and other info we want
        This will filter to a single measurement as well as the expected
        shared columns like depth
        """
        columns = input_df.columns.values
        self._set_column_mappings(input_df)

        columns_to_keep = [
            c for c in columns
            if self._column_mappings[c] in self._measurements_to_keep
        ]
        df = input_df.loc[:, columns_to_keep]
        # Verify the sample column exists and rename to variable
        df = self._check_sample_columns(df)

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

    def _add_thickness_to_df(self):
        # set the thickness of the layer
        if self._has_layers:
            self._df[
                self._meta_parser.primary_variables.entries[
                    "LAYER_THICKNESS"
                ].code
            ] = (
                self._df[self._depth_layer.code] -
                self._df[self._lower_depth_layer.code]
            )

    @property
    def sum(self):
        # get bulk value
        if not self._has_layers:
            # could we assume equidistant spacing and do a mean?
            raise RuntimeError("Cannot compute for no layers")

        # this should work for multi or not multi sample
        profile = self._df.loc[:, self._sample_column]
        self._df["mean"] = profile
        # TODO: sum up with depth change
        # TODO: could we use the weighted mean * the total depth?
        # TODO: units
        pass

    @property
    def mean(self):
        profile = self._df.loc[:, self._sample_column]
        if pd.isna(profile).all():
            return np.nan
        if self._has_layers:
            # height weighted mean for these layers
            thickness = self._df[
                self._meta_parser.primary_variables.entries[
                    "LAYER_THICKNESS"
                ].code
            ]
            # this works for a weighted mean, but is not assumed to be
            # the total thickness of the snowpack
            thickness_total = thickness.sum()
            weighted_mean = (
                profile * thickness / thickness_total
            ).sum()
            value = weighted_mean
        else:
            value = np.mean(profile)

        return value

    @property
    def total_depth(self):
        profile = self._df.loc[:, self._depth_layer.code].values
        return np.nanmax(profile)

    def get_profile(self, snow_datum="ground"):
        # TODO: snow datum is ground or snow
        # get profile of values
        profile_average = self._df.loc[:, self._sample_column]
        df = self._df.copy()
        df[self.variable.code] = profile_average
        columns_of_interest = [*self._non_measure_columns, self.variable.code]
        return df.loc[:, columns_of_interest]


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
            LOG.info(
                'Converting depths in surface datum to snow height format.'
            )

            new = (depths + abs(min_depth))

    elif desired_format == 'surface_datum':
        if is_smp:
            LOG.info('Converting SMP depths to surface datum format.')
            new = depths.mul(-1)

        elif not bottom_is_negative:
            LOG.info(
                'Converting depths in snow height to surface datum format.'
            )
            new = depths - max_depth

    else:
        raise ValueError(
            f'{desired_format} is an invalid depth format! Options are:'
            f' {["snow_height", "surface_datum"]}'
        )

    return new

import logging

import geopandas as gpd
import numpy as np
import pandas as pd

from typing import Union

from insitupy.io.metadata import MetaDataParser
from insitupy.variables import MeasurementDescription

LOG = logging.getLogger(__name__)


class MeasurementData:
    """
    This would be one pit, SMP profile, etc
    Unique date, location, variable
    """
    META_PARSER = MetaDataParser

    def __init__(
        self,
        variable: MeasurementDescription = None,
        meta_parser: MetaDataParser = None,
    ):
        """
        Take df of layered data (SMP, pit)

        Args:
            variable: Description of variable. When None is given, then the
                definitions of the package YAML will be used.
            meta_parser: MetaDataParser object. This will hold our variable
                map and unit map. If no parser is given, then the default
                parser and definition of this package will be used.

        """
        if meta_parser is None:
            meta_parser = self.META_PARSER()
        self._meta_parser = meta_parser

        if variable is None:
            variable = MeasurementDescription()
        self.variable = variable

        # mapping of all column names to a measurement type
        self._column_mappings = {}
        self._sample_column = None

        self._df = None
        self._metadata = None
        # Columns that were identified in via MetaDataParser
        self._meta_columns_map = None

    def _set_column_mappings(self):
        # Get rid of columns we don't want and populate column mapping
        for column in self.columns:
            # Find the variable associated with each column
            # and store a map
            cn, cm = self._meta_parser.primary_variables.from_mapping(column)
            # join with existing mappings
            self._column_mappings = {**cm, **self._column_mappings}

    def _check_sample_columns(self):
        _sample_columns = [
            c for c in self.columns
            if self._column_mappings.get(c) == self.variable
        ]

        if len(_sample_columns) == 0:
            raise ValueError(
                f"No sample columns in {self.columns}. This is likely because"
                f" variable {self.variable} is not in columns"
                f" {self.columns}"
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
        self._df.rename(
            columns={_sample_column: sample_column_type.code},
            inplace=True
        )
        self._sample_column = sample_column_type.code

    @property
    def metadata(self):
        return self._metadata

    @property
    def meta_columns_map(self):
        return self._meta_columns_map

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    @property
    def units_map(self):
        return self._meta_parser.units_map

    @property
    def latlon(self):
        # return location metadata
        return self._metadata.latitude, self._metadata.longitude

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, value):
        self._df = value

        if value.empty:
            LOG.warning("DF is empty")
        else:
            # This will populate the column mapping
            # and filter to the desired measurement column
            self._format_df()

    @property
    def columns(self) -> Union[np.ndarray, None]:
        """
        Gets the column names of the DataFrame if the DataFrame is not None.

        This property method retrieves the column names of the internal
        DataFrame stored in the `_df` attribute.

        Returns:
            numpy.ndarray or None: An array of column names
        """
        if self._df is None:
            return None
        else:
            return self._df.columns.values

    def _format_df(self):
        raise NotImplementedError("not implemented")

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
            df: pd.dataframe of the csv data with desired column names
        """
        raise NotImplementedError("Not implemented")

    def from_csv(self, filename: str):
        """
        Parse all information of a given file, including the header and actual
        data.

        Args:
            filename: (str) Path of a file to read
        """
        # Parse the metadata and column info
        self._metadata, meta_columns, self._meta_columns_map, header_pos = \
            self._meta_parser.parse(filename=filename)

        # read in the actual data
        if meta_columns is None and not self._meta_columns_map:
            # Use an empty dataframe if the file is empty
            LOG.warning(f"File {filename} is empty of rows")
            self.df = pd.DataFrame()
        else:
            self.df = self.read_csv_dataframe(
                filename, meta_columns, header_pos
            )


class ProfileData(MeasurementData):
    """
    This would be one pit, SMP profile, etc
    Unique date, location, variable
    """
    NAN_DATA_VALUE = -9999

    def __init__(
        self,
        variable: MeasurementDescription = None,
        meta_parser: MetaDataParser = None,
    ):
        """
        See MeasurementData.__init__
        """
        # Init the measurement class
        super().__init__(variable=variable, meta_parser=meta_parser)

        # These are our default shared columns
        self._depth_columns = [
            self._meta_parser.primary_variables.entries["DEPTH"],
            self._meta_parser.primary_variables.entries["BOTTOM_DEPTH"]
        ]
        self._depth_layer = self._depth_columns[0]
        self._lower_depth_layer = self._depth_columns[1]
        # List of measurements to keep
        if variable is not None:
            self._measurements_to_keep = (
                self.shared_column_options() + [variable]
            )
        else:
            # If no variable is selected, then we will keep all measurements
            self._measurements_to_keep = []

        # Descriptive internal properties
        self._id = None
        self._dt = None
        self._has_layers = False
        self._non_measure_columns = []

    def shared_column_options(self):
        return self._depth_columns

    def _format_df(self):
        """
        Format the incoming df with the column headers and other info we want
        This will filter to a single measurement as well as the expected
        shared columns like "depth". This will also transform the dataframe
        into a GeoDataFrame with a geometry column from the parsed location in
        the metadata.
        """
        # Filter to the desired measurement columns
        self._set_column_mappings()
        if len(self._measurements_to_keep) > 0:
            columns_to_keep = [
                c for c in self.columns
                if self._column_mappings[c] in self._measurements_to_keep
            ]
            self._df = self._df.loc[:, columns_to_keep]

            # Verify the sample column exists and rename to the selected
            # variable
            self._check_sample_columns()

        self.describe()

        n_entries = len(self._df)
        self._df["datetime"] = [self._dt] * n_entries

        # Prepare location information
        lat, lon = self.latlon
        location = gpd.points_from_xy(
            [lon] * n_entries, [lat] * n_entries
        )

        self._df = gpd.GeoDataFrame(self._df, geometry=location).set_crs(
            "EPSG:4326"
        )
        self._df.replace(self.NAN_DATA_VALUE, np.NaN, inplace=True)

    def _add_thickness_to_df(self) -> None:
        """
        Calculates and adds the thickness column to the given dataframe if
        there is layer depth information.
        """
        self._df[
            self._meta_parser.primary_variables.entries[
                "LAYER_THICKNESS"
            ].code
        ] = (
            self._df[self._depth_layer.code] -
            self._df[self._lower_depth_layer.code]
        )

    def from_csv(self, filename: str):
        """
        See MeasurementData.from_csv
        """
        super().from_csv(filename)

        if len(self.columns) > 0 and self._depth_layer.code not in self.columns:
            raise ValueError(f"Expected {self._depth_layer} in columns")

    def describe(self) -> None:
        """
        Set internal properties based on csv file information and add some
        additional snow depth information if required information is present.
        """
        self._id = self.metadata.site_name
        self._dt = self.metadata.date_time

        # List of columns that are not the desired variable
        _non_measure_columns = [
            self._depth_layer.code,
            self._lower_depth_layer.code,
            "datetime",
            "geometry"
        ]
        # Remember them for later
        self._non_measure_columns = [
            c for c in _non_measure_columns if c in self.columns
        ]

        self._has_layers = self._lower_depth_layer.code in self.columns
        if self._has_layers:
            self._add_thickness_to_df()

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
            thickness = self.df[
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
    for each profile. Desired_format can be:

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

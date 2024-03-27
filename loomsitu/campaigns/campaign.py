"""
Point data from select manual measurement campaigns
"""
import logging
from pathlib import Path
from dataclasses import dataclass
import geopandas as gpd
from typing import List

import pandas as pd

from metloom.pointdata import PointData
from metloom.variables import SensorDescription, VariableBase
from loomsitu.campaigns.metadata import DataHeader

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
    "https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_GM_CSU_GPR.001/2020.02.06/SNEX20_GM_CSU_GPR_1GHz_v01.csv",
    "https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_UNM_GPR.001/2020.01.28/SNEX20_UNM_GPR.csv",
    "https://n5eil01u.ecs.nsidc.org/SNOWEX/SNEX20_SD_TLI.001/2019.09.29/SNEX20_SD_TLI_clean.csv",
]


"""
Start with pit density, temperature measurements

Big pluses
    * variable name mapping

# TODO
    * will need login info for NSIDC
    * stratigraphy will be the most complicated

"""

LOG = logging.getLogger(__name__)


class ProfileVariables(VariableBase):
    SWE = SensorDescription("SWE", "SWE", "Snow Water Equivalent")


@dataclass()
class ProfileMetaData:
    """
    {'site_name': 'East River', 'site_id': 'Aspen',
    'pit_id': 'COERAP_20200427_0845', 'date/local_standard_time':
    '2020-04-27T08:45',
    'utm_zone': 13, 'easting': 329130.6226853253, 'northing': 4310327.542391408,
    'latitude': 38.92524, 'longitude': -106.97112, 'flags': None, 'date': datetime.date(2020, 4, 27), 'time': datetime.time(14, 45, tzinfo=<UTC>), 'epsg': 26913}
    """
    id: str
    date_time: pd.Timestamp
    latitude: float
    longitude: float
    utm_zone: str = None
    site_id: str = None
    site_name: str = None


class ProfileData:
    """
    This would be one pit, SMP profile, etc
    Unique date, location
    # TODO:
    #   Do we make these single variable or provide methods for merging
    #   multiple variables, files, ProfileData to fill out a full df
    """
    def __init__(self, input_df, metadata: ProfileMetaData):
        """
        Take df of layered data (SMP, pit, etc)
        Args:
            input_df: dataframe of data
                Should include depth and optional bottom depth
                Should include sample or sample_a, sample_b, etc

        """
        # TODO: think about implementing a Metadata class
        #   that is more standardized and could be passed in with
        #   required variables for other (non snowex) campaigns
        self._metadata = metadata
        self.variable: ProfileVariables = None

        # TODO: this won't work across profile types - needs to be metadata class
        self._id = metadata.id
        self._dt = metadata.date_time
        self.site_name = metadata.site_name
        self.site_id = metadata.site_id
        self._df = self._format_df(input_df)

    def _format_df(self, input_df):
        """
        Format the incoming df with the column headers and other info we want
        """
        # TODO: check for multi sample (a, b or c in columns)
        n_entries = len(input_df)
        input_df["datetime"] = [self._dt] * n_entries
        lat, lon = self.latlon
        location = gpd.points_from_xy(
            [lon], [lat]
        )
        df = gpd.GeoDataFrame(
            input_df, geometry=location
        ).set_crs("EPSG:4326")
        # TODO: -9999 is nan
        return df

    @property
    def latlon(self):
        # return location metadata
        return self._metadata.info["latitude"], self._metadata.info["longitude"]

    @property
    def df(self):
        return self._df

    def get_value(self, variable: ProfileVariables):
        # get bulk value
        pass

    def get_profile(self, variable, snow_datum="ground"):
        # snow datum is ground or snow
        # get profile of values
        pass

    @property
    def SWE(self):
        """
        Average of samples, then summed with depth to get bulk SWE
        """
        # TODO: how to handle densA, densB, etc
        #       They should be sample_a, sample_b....
        pass

    @classmethod
    def from_file(self, fname, variable: ProfileVariables):
        raise NotImplementedError("Not implemented")


    # def add_profile(self, profile):
    #     # merge this with another of the same class
    #     pass
    #
    # def add_file(self, fname):
    #     # Merge this with another file from the same pit and date
    #     pass
    #
    # def add_df(self, df):
    #     # merge the dfs and metadata
    #     pass

    # def __hash__(self):
    #     # Use to compare if we have something in a list, maybe equality
    #     return f"{self._id}_{self._dt.strftime('%Y%m%d%H%M')}"


class SnowExProfileData(ProfileData):

    def __init__(self, input_df, metadata: DataHeader):
        """
        Take df of layered data (SMP, pit, etc)
        Args:
            input_df: dataframe of data
                Should include depth and optional bottom depth
                Should include sample or sample_a, sample_b, etc

        """
        # TODO: think about implementing a Metadata class
        #   that is more standardized and could be passed in with
        #   required variables for other (non snowex) campaigns
        self._metadata = metadata
        self.variable: ProfileVariables = None

        # TODO: this won't work across profile types - needs to be metadata class
        self._id = metadata.info["pit_id"]
        dt_str = metadata.info["date"].isoformat()
        if metadata.info.get("time"):
            dt_str += f"T{metadata.info['time'].isoformat()}"
        self._dt = pd.to_datetime(dt_str)
        self.site_name = metadata.info["site_name"]
        self.site_id = metadata.info["site_id"]
        self._df = self._format_df(input_df)

    def _format_df(self, input_df):
        """
        Format the incoming df with the column headers and other info we want
        """
        # TODO: check for multi sample (a, b or c in columns)
        dfs = pd.DataFrame()
        n_entries = len(input_df)
        input_df["datetime"] = [self._dt] * n_entries

        # parse the location
        lat, lon = self.latlon
        location = gpd.points_from_xy(
            [lon] * n_entries, [lat] * n_entries
        )
        df = gpd.GeoDataFrame(
            input_df, geometry=location
        ).set_crs("EPSG:4326")
        # TODO: -9999 is nan
        return df

    @classmethod
    def from_file(cls, fname, variable: ProfileVariables):
        # TODO: timezone here (mapped from site?)
        header = DataHeader(fname, in_timezone="US/Mountain")
        dt_str = header.info["date"].isoformat()
        if header.info.get("time"):
            dt_str += f"T{header.info['time'].isoformat()}"
        dt = pd.to_datetime(dt_str)
        metadata = ProfileMetaData(
            id=header.info.
        )
        data = cls._read(fname, metadata)
        return cls(data, metadata)

    @staticmethod
    def _read(profile_filename, metadata):
        """
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
            skiprows=metadata.header_pos,
            names=metadata.columns,
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
                f'File contains {len(metadata.data_names)} profiles each'
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
        variables: List[SensorDescription],
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
    max_depth_at_top = depths.iloc[0] > depths.iloc[-1]

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

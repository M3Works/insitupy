"""
Point data from select manual measurement campaigns
"""
import logging
from pathlib import Path
import geopandas as gpd
from typing import List

import numpy as np
import pandas as pd

from insitupy.io.metadata import MetaDataParser, ProfileMetaData
from insitupy.profiles.base import ProfileData
from insitupy.variables import (
    BasePrimaryVariables, BaseMetadataVariables, MeasurementDescription,
    ExtendableVariables
)
from insitupy.campaigns.snowex import SnowExPrimaryVariables, SnowExMetadataVariables

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


class ProfileDataCollection:
    """
    This could be a collection of pits, profiles, etc
    """
    META_PARSER = MetaDataParser
    PROFILE_DATA_CLASS = ProfileData

    def __init__(self, profiles: List[ProfileData]):
        self._profiles = profiles

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
    def _read(cls, fname, columns, header_pos, metadata):
        # retrun list of ProfileData
        # TODO: read in the df
        # TODO: split into invididual datasets
        # TODO: return a list of profile data from those datasets
        # Iterate columns
        # TODO: rename to standard names for multi sample measurements
        # TODO: share reading logic with ProfileData
        # cls.PROFILE_DATA_CLASS.some_shared_reading_logic
        result = [
            ProfileData(
                df, metadata, variable,  # variable is a MeasurementDescription
                original_file=fname
            )
        ]
        return None

    @classmethod
    def from_csv(cls, fname):
        # TODO: timezone here (mapped from site?)
        # parse mlutiple files and create an iterable of ProfileData
        # TODO: if this is multisample or multi variables,
        #   we should split into n dataframes contained in n objects
        #   (n being sample or variables). This means that we could return
        #   multiple SnowExProfileData instantiated classes for on read
        meta_parser = cls.META_PARSER(fname, "US/Mountain")
        # Parse the metadata and column info
        metadata, columns, header_pos = meta_parser.parse()
        # read in the actual data
        profiles = cls._read(fname, columns, header_pos, metadata)

        # TODO: return a list of classes always

        return cls(profiles, metadata)


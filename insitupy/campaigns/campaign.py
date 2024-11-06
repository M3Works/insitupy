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


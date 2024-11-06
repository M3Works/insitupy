"""
Point data from select manual measurement campaigns
"""
import logging
from typing import List

from insitupy.io.metadata import MetaDataParser, ProfileMetaData
from insitupy.profiles.base import ProfileData
from insitupy.variables import MeasurementDescription


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


LOG = logging.getLogger(__name__)


class ProfileDataCollection:
    """
    This could be a collection of profiles
    """
    META_PARSER = MetaDataParser
    PROFILE_DATA_CLASS = ProfileData

    def __init__(self, profiles: List[ProfileData], metadata: ProfileMetaData):
        self._profiles = profiles
        self._metadata = metadata

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

    @property
    def metadata(self) -> ProfileMetaData:
        return self._metadata

    @property
    def profiles(self) -> List[ProfileData]:
        return self._profiles

    @classmethod
    def _read_csv(
        cls, fname, columns, column_mapping, header_pos,
        metadata: ProfileMetaData
    ) -> List[ProfileData]:
        """
        Args:
            fname: path to csv
            columns: columns for dataframe
            column_mapping: mapping of column name to variable description
            header_pos: skiprows for pd.read_csv
            metadata: metadata for each object

        Returns:
            a list of ProfileData objects

        """
        result = []
        df = cls.PROFILE_DATA_CLASS.read_csv_dataframe(
            fname, columns, header_pos
        )
        # TODO: do we need to add comments in here for shared columns
        depth_columns = cls.PROFILE_DATA_CLASS.depth_columns()
        shared_columns = [
            c for c, v in column_mapping.items() if v in depth_columns
        ]
        variable_columns = [
            c for c in column_mapping.keys() if c not in shared_columns
        ]

        # Create an object for each measurement
        for column in variable_columns:
            target_df = df.loc[:, shared_columns + [column]]
            # We did not auto remap, so do it now
            if not column_mapping[column].auto_remap:

                target_df.rename(
                    columns={column: column_mapping[column].code},
                    inplace=True
                )
            result.append(ProfileData(
                target_df, metadata,
                column_mapping[column],  # variable is a MeasurementDescription
                original_file=fname
            ))

        return result

    @classmethod
    def from_csv(cls, fname):
        # TODO: timezone here (mapped from site?)
        # parse mlutiple files and create an iterable of ProfileData
        meta_parser = cls.META_PARSER(fname, "US/Mountain")
        # Parse the metadata and column info
        metadata, columns, columns_map, header_pos = meta_parser.parse()
        # read in the actual data
        profiles = cls._read_csv(
            fname, columns, columns_map, header_pos, metadata
        )

        return cls(profiles, metadata)


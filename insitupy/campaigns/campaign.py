"""
Point data from select manual measurement campaigns
"""
import logging
from typing import List, Tuple

from insitupy.io.metadata import MetaDataParser, ProfileMetaData
from insitupy.profiles.base import ProfileData
from insitupy.variables import MeasurementDescription

LOG = logging.getLogger(__name__)


class ProfileDataCollection:
    """
    This could be a collection of profiles
    """
    PROFILE_DATA_CLASS = ProfileData

    def __init__(self, profiles: List[ProfileData], metadata: ProfileMetaData):
        self._profiles = profiles
        self._metadata = metadata

    @property
    def SWE(self):
        """
        Takes all layers for each unique date and location and returns point
        swe geo-dataframe. We can iterate though all ProfileData in this class
        and get SWE DF for each
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
        cls,
        filename,
        meta_parser: MetaDataParser,
        shared_column_options=None,
    ) -> Tuple[List[ProfileData], ProfileMetaData]:
        """
        Args:
            filename: path to csv
            meta_parser: metadata parser object
            shared_column_options: shared columns that will be used
                for data handling and storing. These come from primary
                variables but are not the primary data themselves

        Returns:
            a list of ProfileData objects

        """
        result = []

        # Parse the entire file before teasing out individual profiles
        all_profiles = cls.PROFILE_DATA_CLASS(
            variable=None, meta_parser=meta_parser
        )
        all_profiles.from_csv(filename)

        # columns that will be included in data, but are not the primary
        # data themselves
        shared_column_options = shared_column_options or \
            all_profiles.shared_column_options()
        # Filter the shared columns
        shared_columns = [
            c for c, v in all_profiles.meta_columns_map.items()
            if v in shared_column_options
        ]
        # Variable columns are the remaining
        variable_columns = [
            c for c in all_profiles.meta_columns_map.keys()
            if c not in shared_columns
        ]

        # Create an object for each measurement
        for column in variable_columns:
            # Skip columns that are not mapped
            if all_profiles.meta_columns_map[column] is None:
                LOG.debug(f"Skipping column {column} because it is not mapped")
            else:
                profile = cls.PROFILE_DATA_CLASS(
                    meta_parser=meta_parser,
                    variable=all_profiles.meta_columns_map[column],
                )
                # IMPORTANT - Metadata needs to be set before assigning the
                # dataframe as information from the metadata is used to format_df
                # the information
                profile.metadata = all_profiles.metadata
                profile.df = all_profiles.df.loc[:, shared_columns + [column]].copy()
                # --------
                result.append(profile)
        if not result and all_profiles.df.empty:
            # Add one profile if this is empty so we can keep the metadata
            profile = cls.PROFILE_DATA_CLASS(
                meta_parser=meta_parser,
                variable=MeasurementDescription(),
            )
            profile.metadata = all_profiles.metadata
            result.append(profile)

        return result, all_profiles.metadata

    @classmethod
    def from_csv(
        cls,
        filename,
        timezone="US/Mountain",
        header_sep=PROFILE_DATA_CLASS.META_PARSER.DEFAULT_HEADER_SEPARATOR,
        site_id=None,
        campaign_name=None,
        allow_map_failure=False,
        metadata_variable_file=None,
        primary_variable_file=None
    ):
        """
        Find all profiles in a single csv file
        Args:
            filename: path to file
            timezone: expected timezone in file
            header_sep: header sep in the file
            site_id: Site id override for the metadata
            campaign_name: Campaign.name override for the metadata
            allow_map_failure: allow metadata and column unknowns
            metadata_variable_file:
                Optional addition to the recognized metadata variables defined
                in a YAML file
            primary_variable_file:
                Optional addition to the recognized primary variables defined
                in a YAML file
        Returns:
            This class with a collection of profiles and metadata
        """
        # TODO: timezone here (mapped from site?)
        meta_parser = cls.PROFILE_DATA_CLASS.META_PARSER(
            timezone,
            primary_variable_file=primary_variable_file,
            metadata_variable_file=metadata_variable_file,
            header_sep=header_sep,
            _id=site_id,
            campaign_name=campaign_name,
            allow_map_failures=allow_map_failure,
            allow_split_lines=True
        )

        profiles, metadata = cls._read_csv(filename, meta_parser)

        # ignore profiles with the name 'ignore'
        profiles = [
            p for p in profiles if
            # Keep the profile if it is None because we need the metadata
            (p.variable is None or p.variable.code != "ignore")
        ]

        return cls(profiles, metadata)

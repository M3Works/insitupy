from insitupy.campaigns.snowex import SnowExProfileData
from insitupy.profiles.base import ProfileData

from tests.test_helpers import yaml_file_in_list


class TestSnowExCampaign:
    def test_inheritance(self):
        assert issubclass(SnowExProfileData, ProfileData) is True

    def test_default_metadata_variables(self):
        assert yaml_file_in_list(
            'basemetadatavariables',
            SnowExProfileData.DEFAULT_METADATA_VARIABLE_FILES
        )
        assert yaml_file_in_list(
            'snowexmetadatavariables',
            SnowExProfileData.DEFAULT_METADATA_VARIABLE_FILES
        )

    def test_default_primary_variables(self):
        assert yaml_file_in_list(
            'baseprimaryvariables',
            SnowExProfileData.DEFAULT_PRIMARY_VARIABLE_FILES
        )
        assert yaml_file_in_list(
            'snowexprimaryvariables',
            SnowExProfileData.DEFAULT_PRIMARY_VARIABLE_FILES
        )

from profiles.base import MeasurementData, ProfileData
from tests.test_helpers import yaml_file_in_list


class TestProfileData:
    def test_inheritance(self):
        assert issubclass(ProfileData, MeasurementData) is True

    def test_metadata_variable_files(self):
        assert yaml_file_in_list(
            "basemetadatavariables",
            ProfileData.DEFAULT_METADATA_VARIABLE_FILES
        ) is True

    def test_primary_variable_files(self):
        assert yaml_file_in_list(
            "baseprimaryvariables",
            ProfileData.DEFAULT_PRIMARY_VARIABLE_FILES
        ) is True

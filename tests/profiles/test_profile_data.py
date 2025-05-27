from insitupy.profiles.base import MeasurementData, ProfileData
from insitupy.variables.base_variables import MeasurementDescription
from insitupy.io.metadata import MetaDataParser


class TestProfileData:
    def test_inheritance(self):
        assert issubclass(ProfileData, MeasurementData) is True

    def test_init_with_default_arguments(self):
        profile_data = ProfileData()

        assert profile_data.variable is not None
        assert isinstance(profile_data.variable, MeasurementDescription)
        assert profile_data._meta_parser is not None
        assert isinstance(profile_data._meta_parser, MetaDataParser)

    def test_init_default_internal_properties(self):
        profile_data = ProfileData()

        assert [] == profile_data._measurements_to_keep
        assert [] == profile_data._non_measure_columns
        assert False == profile_data._has_layers

    def test_init_with_custom_arguments(self):
        variable = MeasurementDescription(
            code="DEPTH", description="Snow Depth"
        )
        meta_parser = MetaDataParser()
        profile_data = ProfileData(
            variable=variable, meta_parser=meta_parser
        )
        assert profile_data.variable == variable
        assert profile_data._meta_parser == meta_parser

    def test_default_depth_columns_initialization(self):
        profile_data = ProfileData()

        assert profile_data._depth_layer.code == "depth"
        assert profile_data._lower_depth_layer.code == "bottom_depth"

    def test_measurements_to_keep_initialization(self):
        variable = MeasurementDescription(
            code="DEPTH", description="Snow Depth"
        )
        meta_parser = MetaDataParser()
        profile_data = ProfileData(
            variable=variable, meta_parser=meta_parser
        )
        assert variable in profile_data._measurements_to_keep

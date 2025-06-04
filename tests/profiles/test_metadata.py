from insitupy.io.metadata import MetaDataParser
from insitupy.variables import ExtendableVariables, \
    base_metadata_variables_yaml, base_primary_variables_yaml

from tests.test_helpers import yaml_file_in_list


class TestMetaDataParser:
    def test_default_metadata_variables(self):
        assert yaml_file_in_list(
            'basemetadatavariables',
            MetaDataParser.DEFAULT_METADATA_VARIABLE_FILES
        )

    def test_default_primary_variables(self):
        assert yaml_file_in_list(
            'baseprimaryvariables',
            MetaDataParser.DEFAULT_PRIMARY_VARIABLE_FILES
        )

    def test_default_initialization(self):
        """
        Test that the class initializes correctly with default arguments.
        """
        parser = MetaDataParser(timezone="UTC")
        assert parser._input_timezone == "UTC"
        assert parser._header_sep == MetaDataParser.DEFAULT_HEADER_SEPARATOR
        assert parser._campaign_name is None
        assert parser._id is None
        assert [str(base_primary_variables_yaml)] == \
               parser.primary_variables.source_files
        assert [str(base_metadata_variables_yaml)] == \
               parser.metadata_variables.source_files

    def test_custom_initialization(self, yaml_variable_file):
        """
        Test the class initializes with custom arguments.
        """
        primary_overwrite = yaml_variable_file('primary_overwrite.yaml')
        metadata_overwrite = yaml_variable_file('metadata_overwrite.yaml')
        parser = MetaDataParser(
            timezone="US/Mountain",
            primary_variable_file=str(primary_overwrite),
            metadata_variable_file=str(metadata_overwrite),
            header_sep="|",
            allow_split_lines=True,
            allow_map_failures=True,
            _id="1234",
            campaign_name="TestCampaign",
            units_map={"key": "value"}
        )
        assert parser._input_timezone == "US/Mountain"
        assert parser._header_sep == "|"
        assert parser._campaign_name == "TestCampaign"
        assert parser._id == "1234"
        assert parser._allow_split_header_lines is True
        assert str(primary_overwrite) in parser.primary_variables.source_files
        assert str(metadata_overwrite) in parser.metadata_variables.source_files
        assert parser._units_map == {"key": "value"}

    def test_extend_variables_only_default(self, yaml_variable_file):
        yaml_file = yaml_variable_file('variables.yaml')

        result = MetaDataParser.extend_variables([yaml_file])
        assert isinstance(result, ExtendableVariables)
        assert len(result) == 1
        assert not result.allow_map_failures

    def test_extend_variables_with_additions(self, yaml_variable_file):
        yaml_file = yaml_variable_file('variables.yaml')
        additions_file = yaml_variable_file('additions.yaml', 'META_1')

        result = MetaDataParser.extend_variables([yaml_file], additions_file)
        assert isinstance(result, ExtendableVariables)
        assert len(result) == 2

    def test_extend_variables_allow_map_failures(self, yaml_variable_file):
        yaml_file = yaml_variable_file('variables.yaml')

        result = MetaDataParser.extend_variables([yaml_file], allow_map_failures=True)
        assert isinstance(result, ExtendableVariables)
        assert len(result) == 1
        assert result.allow_map_failures

import pandas as pd
import pytest

from insitupy.campaigns.snowex import SnowExMetaDataParser
from insitupy.io.metadata import MetaDataParser
from tests.test_helpers import yaml_file_in_list


class TestSnowMetaDataParser:
    def test_inheritance(self):
        assert issubclass(SnowExMetaDataParser, MetaDataParser) is True

    def test_default_metadata_variables(self):
        assert yaml_file_in_list(
            'basemetadatavariables',
            SnowExMetaDataParser.DEFAULT_METADATA_VARIABLE_FILES
        )
        assert yaml_file_in_list(
            'snowexmetadatavariables',
            SnowExMetaDataParser.DEFAULT_METADATA_VARIABLE_FILES
        )

    def test_default_primary_variables(self):
        assert yaml_file_in_list(
            'baseprimaryvariables',
            SnowExMetaDataParser.DEFAULT_PRIMARY_VARIABLE_FILES
        )
        assert yaml_file_in_list(
            'snowexprimaryvariables',
            SnowExMetaDataParser.DEFAULT_PRIMARY_VARIABLE_FILES
        )


# List of test files with the values as the expected columns to be parsed
# successfully
TEST_FILES = {
    "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv":
        ['depth', 'bottom_depth', 'density_a', 'density_b', 'density_c'],
    "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv":
        ['depth', 'bottom_depth', 'density', 'permittivity_a',
         'permittivity_b', 'lwc_vol_a', 'lwc_vol_b'],
    "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv":
        ['depth', 'snow_temperature']
}


@pytest.fixture(scope="class")
def meta_data_parser():
    return SnowExMetaDataParser(
        "US/Mountain",
        allow_map_failures=True
    )


@pytest.fixture(
    params=list(TEST_FILES.keys()),
    scope="class",
)
def metadata_info(request, meta_data_parser, data_path):
    metadata = meta_data_parser.parse(data_path.joinpath(request.param))
    return metadata, request.param


@pytest.fixture
def metadata(metadata_info):
    return metadata_info[0][0]


@pytest.fixture
def columns(metadata_info):
    return metadata_info[0][1], metadata_info[1]


@pytest.fixture
def header_pos(metadata_info):
    return metadata_info[0][3]


class TestSnowexPitMetadata:
    """
    Test that we can consistently read metadata across
    multiple pit measurements
    """

    def test_id(self, metadata):
        assert metadata.site_name == "COERAP_20200427_0845"

    def test_date_time(self, metadata):
        # converted from mountain time
        assert metadata.date_time == pd.to_datetime(
            "2020-04-27T14:45:00+0000"
        )

    def test_latitude(self, metadata):
        assert metadata.latitude == 38.92524

    def test_longitude(self, metadata):
        assert metadata.longitude == -106.97112

    def test_utm_epsg(self, metadata):
        assert metadata.utm_epsg == '26913'

    def test_site_name(self, metadata):
        assert metadata.campaign_name == "East River"

    def test_flags(self, metadata):
        assert metadata.flags is None

    def test_header_position(self, header_pos):
        assert header_pos == 10

    def test_expected_columns(self, columns):
        assert columns[0] == TEST_FILES[columns[1]]

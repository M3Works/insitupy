import pandas as pd
import pytest

from insitupy.campaigns.snowex import (
    primary_variables_yaml, metadata_variables_yaml
)
from insitupy.variables import (
    ExtendableVariables, base_metadata_variables_yaml,
    base_primary_variables_yaml
)
from insitupy.io.metadata import MetaDataParser



@pytest.mark.parametrize(
    "fname", [
        "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
        "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
        "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv"
    ]
)
class TestSnowexPitMetadata:
    """
    Test that we can consistently read metadata across
    multiple pit measurements
    """

    @pytest.fixture
    def metadata_info(self, fname, data_path):
        # This is the parser object
        obj = MetaDataParser(
            data_path.joinpath(fname),
            "US/Mountain",
            ExtendableVariables(
                [base_primary_variables_yaml, primary_variables_yaml]
            ),
            ExtendableVariables(
                [base_metadata_variables_yaml, metadata_variables_yaml]
            ),
            allow_map_failures=True
        )
        metadata, columns, column_mapping, header_pos = obj.parse()
        return metadata, columns, column_mapping, header_pos

    @pytest.fixture
    def metadata(self, metadata_info):
        return metadata_info[0]

    @pytest.fixture
    def columns(self, metadata_info):
        return metadata_info[1]

    @pytest.fixture
    def header_pos(self, metadata_info):
        return metadata_info[3]

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


@pytest.mark.parametrize(
    "fname, expected_cols", [
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
         ['depth', 'bottom_depth', 'density_a', 'density_b', 'density_c']),
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
         ['depth', 'bottom_depth', 'density', 'permittivity_a',
          'permittivity_b', 'lwc_vol_a', 'lwc_vol_b']),
        ("SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
         ['depth', 'snow_temperature'])
    ]
)
def test_columns(fname, expected_cols, data_path):
    """
    Test the columns we expect to pass back from the file
    """
    obj = MetaDataParser(
        data_path.joinpath(fname),
        "US/Mountain",
        ExtendableVariables(
            [base_primary_variables_yaml, primary_variables_yaml]
        ),
        ExtendableVariables(
            [base_metadata_variables_yaml, metadata_variables_yaml]
        ),
        allow_map_failures=True
    )
    metadata, columns, column_mapping, header_pos = obj.parse()
    assert columns == expected_cols

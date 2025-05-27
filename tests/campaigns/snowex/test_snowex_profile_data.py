import numpy as np
import pytest

from insitupy.campaigns.snowex import SnowExProfileData
from insitupy.variables.base_variables import InputMappingError


class TestSnowexPitProfile:
    """
    Test the attributes of the profile
    """
    @pytest.mark.parametrize(
        "filename, variable", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                "PERMITTIVITY"
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                "DENSITY"
            ),
        ]
    )
    def test_read_fails(
        self, filename, variable, data_path, base_primary_variables
    ):
        file_path = data_path.joinpath(filename)
        with pytest.raises(ValueError):
            SnowExProfileData(
                base_primary_variables.entries[variable],
            ).from_csv(
                file_path
            )

    @pytest.mark.parametrize(
        "filename, variable", [
            (
                "Density_file_unmapped.csv",
                "DENSITY"
            ),
        ]
    )
    def test_read_fails_mapping_error(
        self, filename, variable, data_path, base_primary_variables
    ):
        """
        Test that we fail to map a column in the column names when
        we expect them all to be mapped
        """
        file_path = data_path.joinpath(filename)
        with pytest.raises(InputMappingError):
            SnowExProfileData(
                base_primary_variables.entries[variable],
            ).from_csv(
                file_path
            )

    @pytest.mark.parametrize(
        "filename, variable, expected", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
                "SNOW_TEMPERATURE",
                0.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                "LWC_A",
                np.nan
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                "PERMITTIVITY_A",
                np.nan
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                "DENSITY_A",
                397.8888888
            ),
        ]
    )
    def test_mean(
        self, filename, variable, expected, data_path, base_primary_variables
    ):
        file_path = data_path.joinpath(filename)
        obj = SnowExProfileData(base_primary_variables.entries[variable])
        obj.from_csv(file_path)
        result = obj.mean

        if np.isnan(expected):
            assert np.isnan(result)
        else:
            assert result == pytest.approx(expected)

    @pytest.mark.parametrize(
        "filename, variable, expected", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
                "SNOW_TEMPERATURE",
                95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                "LWC_A",
                95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                "PERMITTIVITY_B",
                95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                "DENSITY_A",
                95.0
            ),
        ]
    )
    def test_total_depth(
        self, filename, variable, expected, data_path, base_primary_variables
    ):
        file_path = data_path.joinpath(filename)
        obj = SnowExProfileData(base_primary_variables.entries[variable])
        obj.from_csv(file_path)
        result = obj.total_depth

        assert result == pytest.approx(expected)

import numpy as np
import pytest

from insitupy.campaigns.snowex import SnowExProfileData
from insitupy.variables import BasePrimaryVariables


class TestSnowexPitProfile:
    """
    Test the attributes of the profile
    """

    @pytest.mark.parametrize(
        "fname, variable", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                BasePrimaryVariables.PERMITTIVITY
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                BasePrimaryVariables.DENSITY
            ),
        ]
    )
    def test_read_fails(self, fname, variable, data_path):
        file_path = data_path.joinpath(fname)
        with pytest.raises(ValueError):
            SnowExProfileData.from_csv(
                file_path, variable, allow_map_failures=True
            )

    @pytest.mark.parametrize(
        "fname, variable", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                BasePrimaryVariables.PERMITTIVITY
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                BasePrimaryVariables.DENSITY
            ),
        ]
    )
    def test_read_fails_mapping_error(self, fname, variable, data_path):
        file_path = data_path.joinpath(fname)
        with pytest.raises(RuntimeError):
            SnowExProfileData.from_csv(
                file_path, variable, allow_map_failures=False
            )

    @pytest.mark.parametrize(
        "fname, variable, expected", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
                BasePrimaryVariables.SNOW_TEMPERATURE, 0.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                BasePrimaryVariables.LWC_A, np.nan
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                BasePrimaryVariables.PERMITTIVITY_A, np.nan
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                BasePrimaryVariables.DENSITY_A, 397.8888888
            ),
        ]
    )
    def test_mean(self, fname, variable, expected, data_path):
        file_path = data_path.joinpath(fname)
        obj = SnowExProfileData.from_csv(
            file_path, variable, allow_map_failures=True
        )
        result = obj.mean
        if np.isnan(expected):
            assert np.isnan(result)
        else:
            assert result == pytest.approx(expected)

    @pytest.mark.parametrize(
        "fname, variable, expected", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
                BasePrimaryVariables.SNOW_TEMPERATURE, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                BasePrimaryVariables.LWC_A, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                BasePrimaryVariables.PERMITTIVITY_B, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                BasePrimaryVariables.DENSITY_A, 95.0
            ),
        ]
    )
    def test_total_depth(self, fname, variable, expected, data_path):
        file_path = data_path.joinpath(fname)
        obj = SnowExProfileData.from_csv(
            file_path, variable, allow_map_failures=True
        )
        result = obj.total_depth
        assert result == pytest.approx(expected)

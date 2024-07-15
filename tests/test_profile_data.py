import numpy as np
import pytest

from insitupy.campaigns.campaign import SnowExProfileData
from insitupy.campaigns.variables import ProfileVariables


class TestSnowexPitProfile:
    """
    Test the attributes of the profile
    """

    @pytest.mark.parametrize(
        "fname, variable, expected", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
                ProfileVariables.SNOW_TEMPERATURE, 0.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                ProfileVariables.LWC, np.nan
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                ProfileVariables.PERMITTIVITY, np.nan
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                ProfileVariables.DENSITY, 395.037037
            ),
        ]
    )
    def test_mean(self, fname, variable, expected, data_path):
        file_path = data_path.joinpath(fname)
        obj = SnowExProfileData.from_file(file_path, variable)
        result = obj.mean
        if np.isnan(expected):
            assert np.isnan(result)
        else:
            assert result == pytest.approx(expected)

    @pytest.mark.parametrize(
        "fname, variable, expected", [
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
                ProfileVariables.SNOW_TEMPERATURE, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                ProfileVariables.LWC, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
                ProfileVariables.PERMITTIVITY, 95.0
            ),
            (
                "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
                ProfileVariables.DENSITY, 95.0
            ),
        ]
    )
    def test_total_depth(self, fname, variable, expected, data_path):
        file_path = data_path.joinpath(fname)
        obj = SnowExProfileData.from_file(file_path, variable)
        result = obj.total_depth
        assert result == pytest.approx(expected)

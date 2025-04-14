import pytest
import numpy as np

from insitupy.campaigns.snowex import SnowExProfileDataCollection
from . import BASE_PRIMARY_VARIABLES


@pytest.mark.parametrize(
    "fname, expected_variables, expected_means", [
        (
            "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv",
            [BASE_PRIMARY_VARIABLES.entries["SNOW_TEMPERATURE"]], [0.0]
        ),
        (
            "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv",
            [
                BASE_PRIMARY_VARIABLES.entries["DENSITY"],
                BASE_PRIMARY_VARIABLES.entries["PERMITTIVITY_A"],
                BASE_PRIMARY_VARIABLES.entries["PERMITTIVITY_B"],
                BASE_PRIMARY_VARIABLES.entries["LWC_A"],
                BASE_PRIMARY_VARIABLES.entries["LWC_B"],
            ], [395.03703703703707, np.nan, np.nan, np.nan, np.nan]
        ),
        (
            "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv",
            [
                BASE_PRIMARY_VARIABLES.entries["DENSITY_A"],
                BASE_PRIMARY_VARIABLES.entries["DENSITY_B"],
                BASE_PRIMARY_VARIABLES.entries["DENSITY_C"]
            ],
            [397.8888888, 394.5555556, 137.1111111]
        ),
    ]
)
class TestProfileDataCollection:
    @pytest.fixture
    def obj(self, fname, data_path):
        file_path = data_path.joinpath(fname)
        obj = SnowExProfileDataCollection.from_csv(
            file_path, allow_map_failure=True
        )
        return obj

    def test_variables(self, obj, expected_variables, expected_means):
        result_variables = [
            p.variable for p in obj.profiles
        ]
        assert result_variables == expected_variables

    def test_mean(self, obj, expected_variables, expected_means):
        result_means = [
            p.mean for p in obj.profiles
        ]
        np.testing.assert_almost_equal(
            np.array(result_means), np.array(expected_means)
        )

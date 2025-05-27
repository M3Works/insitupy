import numpy as np
import pytest

from insitupy.campaigns import ProfileDataCollection
from insitupy.campaigns.snowex import SnowExProfileData, \
    SnowExProfileDataCollection

TEST_FILES = {
    "SNEX20_TS_SP_20200427_0845_COERAP_data_temperature_v01.csv":
        {
            'variables': ["SNOW_TEMPERATURE"],
            'means': [0.0]
        },
    "SNEX20_TS_SP_20200427_0845_COERAP_data_LWC_v01.csv":
        {
            'variables':
                [
                    "DENSITY",
                    "PERMITTIVITY_A",
                    "PERMITTIVITY_B",
                    "LWC_A",
                    "LWC_B",
                ],
            'means': [395.03703703703707, np.nan, np.nan, np.nan, np.nan]
        },
    "SNEX20_TS_SP_20200427_0845_COERAP_data_density_v01.csv":
        {
            'variables':
                [
                    "DENSITY_A",
                    "DENSITY_B",
                    "DENSITY_C"
                ],
            'means': [397.8888888, 394.5555556, 137.1111111]
        },
}


class TestSnowExProfileDataCollection:
    def test_inheritance(self):
        assert issubclass(SnowExProfileDataCollection, ProfileDataCollection) \
            is True

    def test_profile_data_class(self):
        assert SnowExProfileDataCollection.PROFILE_DATA_CLASS == \
            SnowExProfileData


@pytest.fixture
def data_collection(data_path):
    def _create_obj(filename):
        file_path = data_path.joinpath(filename)
        return SnowExProfileDataCollection.from_csv(
            file_path, allow_map_failure=True
        )
    yield _create_obj


@pytest.mark.parametrize('test_file', TEST_FILES)
class TestSnowExProfileDataCollectionFromCSV:
    def test_variables(
        self, test_file, data_collection, base_primary_variables
    ):
        obj = data_collection(test_file)
        result_variables = [p.variable for p in obj.profiles]
        expected_variables = [
            base_primary_variables.entries[entry]
            for entry in TEST_FILES[test_file]['variables']
        ]

        assert result_variables == expected_variables

    def test_mean(self, test_file, data_collection, base_primary_variables):
        obj = data_collection(test_file)
        result_means = [
            p.mean for p in obj.profiles
        ]
        np.testing.assert_almost_equal(
            np.array(result_means),
            np.array(TEST_FILES[test_file]['means']),
            decimal=2
        )

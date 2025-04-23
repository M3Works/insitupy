from insitupy.campaigns import ProfileDataCollection
from insitupy.campaigns.snowex import (SnowExProfileData,
                                       SnowExProfileDataCollection)


class TestSnowExProfileDataCollection:
    def test_inheritance(self):
        assert issubclass(SnowExProfileDataCollection, ProfileDataCollection) \
            is True

    def test_profile_data_class(self):
        assert SnowExProfileDataCollection.PROFILE_DATA_CLASS == \
            SnowExProfileData

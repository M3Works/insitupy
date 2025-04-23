from insitupy.campaigns import ProfileDataCollection
from insitupy.io.metadata import MetaDataParser
from insitupy.profiles.base import ProfileData


class TestProfileDataCollection:
    def test_profile_data_class(self):
        assert ProfileDataCollection.PROFILE_DATA_CLASS == ProfileData

    def test_metadata_data_class(self):
        assert ProfileDataCollection.META_PARSER == MetaDataParser

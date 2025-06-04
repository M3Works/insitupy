from insitupy.campaigns.snowex import SnowExProfileData
from insitupy.profiles.base import ProfileData


class TestSnowExCampaign:
    def test_inheritance(self):
        assert issubclass(SnowExProfileData, ProfileData) is True

from insitupy.campaigns import ProfileDataCollection
from .snowex_campaign import SnowExProfileData


class SnowExProfileDataCollection(ProfileDataCollection):
    PROFILE_DATA_CLASS = SnowExProfileData

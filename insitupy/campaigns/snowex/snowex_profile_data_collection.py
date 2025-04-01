from insitupy.campaigns import ProfileDataCollection
from .snowex_campaign import SnowExProfileData


class SnowExProfileDataCollection(ProfileDataCollection):
    PROFILE_DATA_CLASS = SnowExProfileData
    DEFAULT_METADATA_VARIABLE_FILES = PROFILE_DATA_CLASS.DEFAULT_METADATA_VARIABLE_FILES
    DEFAULT_PRIMARY_VARIABLE_FILES = PROFILE_DATA_CLASS.DEFAULT_PRIMARY_VARIABLE_FILES

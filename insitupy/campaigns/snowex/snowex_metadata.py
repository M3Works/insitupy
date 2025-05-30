from .variables import snowex_metadata_yaml, snowex_variables_yaml
from insitupy.io.metadata import MetaDataParser
from insitupy.variables import base_metadata_variables_yaml, \
    base_primary_variables_yaml


class SnowExMetaDataParser(MetaDataParser):
    """
    Base class for parsing SnowEx metadata header information and column names.
    """
    DEFAULT_METADATA_VARIABLE_FILES = [
        base_metadata_variables_yaml, snowex_metadata_yaml
    ]
    DEFAULT_PRIMARY_VARIABLE_FILES = [
        base_primary_variables_yaml, snowex_variables_yaml
    ]

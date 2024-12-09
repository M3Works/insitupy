from insitupy.variables.base_metadata_variables import BaseMetadataVariables
from insitupy.variables.base_variables import MeasurementDescription


class SnowExMetadataVariables(BaseMetadataVariables):
    """
    Extend the metadata variables to include more mappings
    for snowex
    """
    TOTAL_DEPTH = MeasurementDescription(
        'total_depth', "Total depth of measurement",
        ['total_snow_depth'], auto_remap=True
    )
    LATITUDE = MeasurementDescription(
        'latitude', "Latitude",
        ['lat', 'latitude'], auto_remap=True
    )
    LONGITUDE = MeasurementDescription(
        'longitude', "Longitude",
        ['long', 'lon', 'longitude'], auto_remap=True
    )
    NORTHING = MeasurementDescription(
        'northing', "UTM Northing",
        ['northing', 'utm_wgs84_northing'], auto_remap=True
    )
    EASTING = MeasurementDescription(
        'easting', "UTM Easting",
        ['easting', 'utm_wgs84_easting'], auto_remap=True
    )
    UTM_ZONE = MeasurementDescription(
        'utm_zone', "UTM Zone",
        ['utmzone', 'utm_zone'], auto_remap=True
    )
    ELEVATION = MeasurementDescription(
        'elevation', "Elevation",
        ['elev_m', 'elevation', 'elevationwgs84'], auto_remap=True
    )

from insitupy.variables.base_metadata_variables import BaseMetadataVariables
from insitupy.variables.base_variables import MeasurementDescription


class SnowExMetadataVariables(BaseMetadataVariables):
    """
    Extend the metadata variables to include more mappings
    for snowex
    """
    TOTAL_DEPTH = MeasurementDescription(
        'total_depth', "Total depth of measurement",
        ['total_snow_depth']
    )
    LATITUDE = MeasurementDescription(
        'latitude', "Latitude",
        ['lat', 'latitude']
    )
    LONGITUDE = MeasurementDescription(
        'longitude', "Longitude",
        ['long', 'lon', 'longitude']
    )
    NORTHING = MeasurementDescription(
        'northing', "UTM Northing",
        ['northing', 'utm_wgs84_northing'], True
    )
    EASTING = MeasurementDescription(
        'easting', "UTM Easting",
        ['easting', 'utm_wgs84_easting'], True
    )
    UTM_ZONE = MeasurementDescription(
        'utm_zone', "UTM Zone",
        ['utmzone', 'utm_zone']
    )
    ELEVATION = MeasurementDescription(
        'elevation', "Elevation",
        ['elev_m', 'elevation', 'elevationwgs84'], True
    )

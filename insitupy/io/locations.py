import logging
from typing import Tuple, Union

import utm

from .yaml_codes import YamlCodes

LOG = logging.getLogger(__name__)


class LocationManager:
    NORTHERN_HEMISPHERE = True

    @classmethod
    def parse_from_headers(cls, headers: dict) -> Tuple[
        float, float, Union[str, None], Union[str, None]
    ]:
        """
        Initial parse of lat, lon, easting, northing from the headers object

        Args:
            headers (dict): Parsed header with key-value pairs

        Returns:
            (Tuple) Latitude, Longitude, Easting, Northing
        """
        latitude = headers.get(YamlCodes.LATITUDE, None)
        longitude = headers.get(YamlCodes.LONGITUDE, None)
        easting = headers.get(YamlCodes.EASTING, None)
        northing = headers.get(YamlCodes.NORTHING, None)

        latitude = float(latitude) if latitude is not None else latitude
        longitude = float(longitude) if longitude is not None else longitude

        return latitude, longitude, easting, northing

    @classmethod
    def lat_lon_from_easting_northing(
        cls, headers: dict, easting: str, northing: str
    ) -> Tuple:
        """
        Convert Easting and Northing information to Lat/Lon objects via utm

        Args:
            headers (dict): Parsed header with key-value pairs
            easting (str): Detected Easting information
            northing (str): Detected Northing information

        Returns:
            (Tuple) Latitude, Longitude objects
        """
        zone_number = cls.parse_utm_epsg(headers)

        if isinstance(zone_number, str):
            raise RuntimeError(f"{zone_number} should be an integer")

        # Get the last two digits
        zone_number = int(str(zone_number)[-2:])
        try:
            lat, lon = utm.to_latlon(
                float(easting),
                float(northing),
                int(zone_number),
                northern=cls.NORTHERN_HEMISPHERE
            )
        except Exception as e:
            LOG.error(e)
            raise RuntimeError(f"Failed with {easting}, {northing}")

        return lat, lon

    @classmethod
    def parse(cls, headers: dict) -> Tuple[str, str, str, str]:
        """
        Parse the lat and lon from the header object

        Also parse the easting and northing
        # UTM Zone,13N
        # Easting,329131
        # Northing,4310328
        # Latitude,38.92524
        # Longitude,-106.97112
        # Flags,

        returns lat, lon, easting, northing
        """
        lat, lon, easting, northing = cls.parse_from_headers(headers)

        # Do nothing first
        if lat and lon:
            LOG.info("Latitude and Longitude parsed from the file header")
        elif easting and northing:
            LOG.info(
                "Latitude and Longitude converted from easting and northing"
            )
            lat, lon = cls.lat_lon_from_easting_northing(
                headers, easting, northing
            )
        else:
            raise ValueError(f"Could not parse location from {headers}")

        return lat, lon, easting, northing

    @classmethod
    def parse_utm_epsg(cls, headers: dict) -> Union[int | None]:
        # TODO: headers based utm?
        if YamlCodes.UTM_ZONE in headers.keys():
            utm_zone = int(
                ''.join(
                    [c for c in headers[YamlCodes.UTM_ZONE] if c.isnumeric()]
                )
            )
            return int(f"{YamlCodes.UTM_EPSG_PREFIX}{utm_zone}")
        elif YamlCodes.EPSG in headers.keys():
            return int(headers[YamlCodes.EPSG])
        else:
            LOG.warning(
                f"Could not find UTM keys in headers: {headers.keys()}"
            )
            return None

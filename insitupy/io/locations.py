import logging
import utm
from typing import Tuple

LOG = logging.getLogger(__name__)


class LocationManager:
    LAT_NAMES = ["lat", "latitude"]
    LON_NAMES = ["lon", "lon", "longitude"]
    UTM_EPSG_PREFIX = "269"
    NORTHERN_HEMISPHERE = True

    @classmethod
    def parse_location_from_raw(cls, headers: dict) -> Tuple[str, str, str, str]:
        """
        Initial parse of lat, lon, easting, northing from the headers object

        Args:
            headers (dict): Parsed header headerss with key-value pairs

        Returns:
            (Tuple) Latitude, Longitude, Easting, Northing
        """
        lat = None
        lon = None
        easting = None
        northing = None

        for k, v in headers.items():
            if k in cls.LAT_NAMES:
                lat = float(v)
            elif k in cls.LON_NAMES:
                lon = float(v)
            elif k == "easting":
                easting = v
            elif k == "northing":
                northing = v

        return lat, lon, easting, northing

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
            raise RuntimeError(
                f"{zone_number} should be an integer"
            )

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
        lat, lon, easting, northing = cls.parse_location_from_raw(headers)

        # Do nothing first
        if lat and lon:
            LOG.info("Latitude and Longitude parsed from the file")
        elif easting and northing:
            lat, lon = cls.lat_lon_from_easting_northing(
                headers, easting, northing
            )
        else:
            raise ValueError(f"Could not parse location from {headers}")
        return lat, lon, easting, northing

    @classmethod
    def parse_utm_epsg(cls, headers: dict) -> int | None:
        # TODO: headers based utm?
        if 'utm_zone' in headers.keys():
            utm_zone = int(
                ''.join([c for c in headers['utm_zone'] if c.isnumeric()])
            )
            return int(f"{cls.UTM_EPSG_PREFIX}{utm_zone}")
        elif 'epsg' in headers.keys():
            return int(headers["epsg"])

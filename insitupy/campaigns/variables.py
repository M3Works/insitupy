import inspect
import logging
from dataclasses import dataclass
from typing import List


LOG = logging.getLogger(__name__)


# Similar to MeasurementDescription from metloom
@dataclass(eq=True, frozen=True)
class MeasurementDescription:
    """
    data class for describing a measurement
    """

    code: str = "-1"  # code used within the applicable API
    description: str = None  # description of the sensor
    map_from: List = None  # map to this variable from a list of options
    remap: bool = False  # Auto remap to the column to the code
    # TODO: optional unit we get form 'parse_from' method
    # unit: str = None
    cast_type = None   # make this float, int, etc


class ExtendableVariables:
    """
    Make a class with the helpful iterator portion of enums, but
    that is fully extendable
    """
    def __init__(self, entries=None):
        self._entries = None
        # allows filtering to a desired list
        self._initial_entries = entries or self._all_variables

    @property
    def entries(self):
        if self._entries is None:
            self._entries = self._get_members()
        return self._entries

    @property
    def _all_variables(self):
        return [m[1] for m in self.entries]

    @property
    def variables(self):
        return [m[1] for m in self.entries if m[1] in self._initial_entries]

    @property
    def names(self):
        return [m[0] for m in self.entries if m[1] in self._initial_entries]

    @classmethod
    def _get_members(cls):
        """
        https://www.geeksforgeeks.org/how-to-get-a-list-of-class-attributes-in-python/
        Important this is a class method or seg faults
        """
        result = []
        # getmembers() returns all the
        # members of an object
        for i in inspect.getmembers(cls):

            # to remove private and protected
            # functions
            if not i[0].startswith('_'):

                # To remove other methods that
                # doesnot start with a underscore
                if not inspect.ismethod(i[1]) and not isinstance(i[1], property):
                    result.append(i)
        return result

    def __iter__(self):
        for item in self.variables:
            yield item

    def __len__(self):
        return len(self.entries)

    # TODO: value mapping for casting
    @classmethod
    def from_mapping(cls, input_name):
        """
        Get the measurement description from an input name.
        This will use the  MeasurementDescription.map_from list to
        check, in order, which variable we should use

        Returns:
            column name
            column mapping (map of name to MeasurementDescription)
        """
        result = None
        # Map column name to variable type
        column_mapping = {}
        for entry in cls():
            if entry.map_from and input_name.lower() in entry.map_from:
                # Remap to code
                if entry.remap:
                    result = entry.code
                else:
                    result = input_name
                column_mapping[result] = entry
                break
        if result is None:
            raise RuntimeError(f"Could not find mapping for {input_name}")
        LOG.debug(
            f"Mapping {result} to {result} (type {column_mapping[result]})"
        )
        return result, column_mapping


class ProfileVariables(ExtendableVariables):

    SWE = MeasurementDescription(
        "SWE", "Snow Water Equivalent",
        ["swe_mm", "swe"]
    )
    DEPTH = MeasurementDescription(
        "depth", "top or center depth of measurement",
        [
            "depth", "top", "sample_top_height", "hs",
            "depth_m", 'snowdepthfilter(m)', 'snowdepthfilter',
            'height'
        ], True
    )
    BOTTOM_DEPTH = MeasurementDescription(
        "bottom_depth", "Lower edge of measurement",
        ["bottom", "bottom_depth"], True
    )
    DENSITY = MeasurementDescription(
        "density", "measured snow density",
        [
            "density", "density_a", "density_b", "density_c", "avg_density",
            "avgdensity", 'density_mean'
        ]
    )
    LAYER_THICKNESS = MeasurementDescription(
        "layer_thickness", "thickness of layer"
    )
    SNOW_TEMPERATURE = MeasurementDescription(
        "snow_temperature", "Snowpack Temperature",
        ["temperature", "temperature_deg_c"]
    )
    LWC = MeasurementDescription(
        "liquid_water_content", "Liquid water content",
        ["lwc_vol_a", "lwc_vol_b", "lwc", "lwc_vol"]
    )
    PERMITTIVITY = MeasurementDescription(
        "permittivity", "Permittivity",
        ["permittivity_a", "permittivity_b", "permittivity",
         'dielectric_constant', 'dielectric_constant_a',
         'dielectric_constant_b'], True
    )
    GRAIN_SIZE = MeasurementDescription(
        "grain_size", "Grain Size",
        ["grain_size"]
    )
    GRAIN_TYPE = MeasurementDescription(
        "grain_type", "Grain Type",
        ["grain_type"]
    )
    HAND_HARDNESS = MeasurementDescription(
        "hand_hardness", "Hand Hardness",
        ["hand_hardness"]
    )
    MANUAL_WETNESS = MeasurementDescription(
        "manual_wetness", "Manual Wetness",
        ["manual_wetness"]
    )


class SnowExProfileVariables(ProfileVariables):
    # TODO: Some of these move to snowexdb
    # TODO: unify with snowexdb
    DATETIME = MeasurementDescription(
        'datetime', "Combined date and time",
        ["Date/Local Standard Time", "date/local_standard_time", "datetime",
         "date&time"],
        True
    )
    DATE = MeasurementDescription(
        'date', "Measurement Date (only date column)",
        ['date_dd_mmm_yy', 'date']
    )
    TIME = MeasurementDescription(
        'time', "Measurement time",
        ['time_gmt', 'time']
    )
    TIME_BOUND_PIT = MeasurementDescription(
        "Time start/end",
        "Time of first or last pit measurement",
        ["Time start/end", "time_start/end"]
    )
    SITE_NAME = MeasurementDescription(
        "site_name", "Name of campaign site",
        ['location'], True
    )
    SITE_ID = MeasurementDescription(
        "site_id", "ID within campaign site",
        ['site'], True
    )
    PIT_ID = MeasurementDescription(
        "pit_id", "ID of snow pit",
        ['pitid'], True
    )
    EQUIVALENT_DIAMETER = MeasurementDescription(
        'equivalent_diameter', "",
        ['deq']
    )

    TOTAL_DEPTH = MeasurementDescription(
        'total_depth', "Total depth of measurement",
        ['total_snow_depth']
    )
    INSTRUMENT = MeasurementDescription(
        'instrument', "Instrument of measurement",
        ['smp_serial_number', 'measurement_tool', 'instrument']
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


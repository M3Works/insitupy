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


class ProfileVariables(ExtendableVariables):
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

    SWE = MeasurementDescription(
        "SWE", "Snow Water Equivalent",
        ["swe_mm", "swe"]
    )
    DEPTH = MeasurementDescription(
        "depth", "top or center depth of measurement",
        [
            "depth", "top", "sample_top_height", "hs",
            "depth_m", 'snowdepthfilter(m)'
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
        ["permittivity_a", "permittivity_b", "permittivity", 'dielectric_constant']
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
    COMMENTS = MeasurementDescription(
        "comments", "Comments",
        ["comments"]
    )
    PIT_COMMENTS = MeasurementDescription(
        "pit_comments", "Pit Comments",
        ["pit_comments"]
    )
    COUNT = MeasurementDescription(
        "count", "Count for surrounding perimeter depths",
        ["count"]
    )
    PARAMETER_CODES = MeasurementDescription(
        "parameter_codes", "Parameter Codes",
        ["parameter_codes"]
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
    OBSERVERS = MeasurementDescription(
        'observers', "Observer(s) of the measurement",
        ['operator', 'surveyors', 'observer']
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
    EASTING = MeasurementDescription(
        'easting', "UTM Easting",
        ['easting']
    )
    NORTHING = MeasurementDescription(
        'northing', "UTM Northing",
        ['northing']
    )
    TWO_WAY_TRAVEL = MeasurementDescription(
        'two_way_travel', "Two way travel",
        ['twt', 'twt_ns']
    )
    UTM_ZONE = MeasurementDescription(
        'utm_zone', "UTM Zone",
        ['utmzone', 'utm_zone']
    )
    FLAGS = MeasurementDescription(
        'flags', "Measurements flags",
        ['flag']
    )
    DATE = MeasurementDescription(
        'date', "Measurement Date (only date column)",
        ['date_dd_mmm_yy']
    )
    TIME = MeasurementDescription(
        'time', "Measurement time",
        ['time_gmt']
    )
    ELEVATION = MeasurementDescription(
        'elevation', "Elevation",
        ['elev_m']
    )
    DATETIME = MeasurementDescription(
        'datetime', "Combined date and time",
        ["Date/Local Standard Time", "date/local_standard_time", "datetime"],
        True
    )
    RH_10FT = MeasurementDescription(
        "relative_humidity_10ft",
        "Relative humidity measured at 10 ft tower level",
        ['rh_10ft']
    )
    BP = MeasurementDescription(
        'barometric_pressure', "Barometric pressure",
        ['bp_kpa_avg']
    )
    AIR_TEMP_10FT = MeasurementDescription(
        'air_temperature_10ft',
        "Air temperature measured at 10 ft tower level",
        ['airtc_10ft_avg']
    )
    WIND_SPEED_10FT = MeasurementDescription(
        'wind_speed_10ft',
        "Vector mean wind speed measured at 10 ft tower level",
        ['wsms_10ft_avg']
    )
    WIND_DIR_10ft = MeasurementDescription(
        'wind_direction_10ft',
        "Vector mean wind direction measured at 10 ft tower level",
        ['winddir_10ft_d1_wvt']
    )
    SW_IN = MeasurementDescription(
        'incoming_shortwave',
        "Shortwave radiation measured with upward-facing sensor",
        ['sup_avg']
    )
    SW_OUT = MeasurementDescription(
        'outgoing_shortwave',
        "Shortwave radiation measured with downward-facing sensor",
        ['sdn_avg']
    )
    LW_IN = MeasurementDescription(
        'incoming_longwave',
        "Longwave radiation measured with upward-facing sensor",
        ['lupco_avg']
    )
    LW_OUT = MeasurementDescription(
        'outgoing_longwave',
        "Longwave radiation measured with downward-facing sensor",
        ['ldnco_avg']
    )
    SM_20CM = MeasurementDescription(
        'soil_moisture_20cm', "Soil moisture measured at 10 cm below the soil",
        ['sm_20cm_avg']
    )
    ST_20CM = MeasurementDescription(
        'soil_temperature_20cm',
        "Soil temperature measured at 10 cm below the soil",
        ['tc_20cm_avg']
    )

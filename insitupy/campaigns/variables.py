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
    name: str = "basename"  # desired name for the sensor
    description: str = None  # description of the sensor
    map_from: List = None  # map to this variable from a list of options
    remap: bool = False  # Auto remap to the column to the code


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
        "SWE", "SWE", "Snow Water Equivalent",
        ["swe_mm", "swe"]
    )
    # TODO: more variables
    #   Next up is Grain Size (mm),Grain Type,Hand Hardness,Manual Wetness,Comments
    DEPTH = MeasurementDescription(
        "depth", "depth", "top or center depth of measurement",
        ["depth", "top", "sample_top_height", "hs", "depth_m"], True
    )
    BOTTOM_DEPTH = MeasurementDescription(
        "bottom_depth", "bottom_depth", "Lower edge of measurement",
        ["bottom", "bottom_depth"], True
    )
    DENSITY = MeasurementDescription(
        "density", "density", "measured snow density",
        ["density", "density_a", "density_b", "density_c", "avg_density"]
    )
    LAYER_THICKNESS = MeasurementDescription(
        "layer_thickness", "layer_thickness", "thickness of layer"
    )
    SNOW_TEMPERATURE = MeasurementDescription(
        "snow_temperature", "snow_temperature", "Snowpack Temperature",
        ["temperature", "temperature_deg_c"]
    )
    LWC = MeasurementDescription(
        "liquid_water_content", "liquid_water_content", "Liquid water content",
        ["lwc_vol_a", "lwc_vol_b", "lwc", "lwc_vol"]
    )
    PERMITTIVITY = MeasurementDescription(
        "permittivity", "permittivity", "Permittivity",
        ["permittivity_a", "permittivity_b", "permittivity"]
    )
    GRAIN_SIZE = MeasurementDescription(
        "grain_size", "grain_size", "Grain Size",
        ["grain_size"]
    )
    GRAIN_TYPE = MeasurementDescription(
        "grain_type", "grain_type", "Grain Type",
        ["grain_type"]
    )
    HAND_HARDNESS = MeasurementDescription(
        "hand_hardness", "hand_hardness", "Hand Hardness",
        ["hand_hardness"]
    )
    MANUAL_WETNESS = MeasurementDescription(
        "manual_wetness", "manual_wetness", "Manual Wetness",
        ["manual_wetness"]
    )


class SnowExProfileVariables(ProfileVariables):
    COMMENTS = MeasurementDescription(
        "comments", "comments", "Comments",
        ["comments"]
    )
    PIT_COMMENTS = MeasurementDescription(
        "pit_comments", "pit_comments", "Pit Comments",
        ["pit_comments"]
    )
    COUNT = MeasurementDescription(
        "count", "count", "Count for surrounding perimeter depths",
        ["count"]
    )
    PARAMETER_CODES = MeasurementDescription(
        "parameter_codes", "parameter_codes", "Parameter Codes",
        ["parameter_codes"]
    )
    TIME_BOUND_PIT = MeasurementDescription(
        "Time start/end", "Time start/end",
        "Time of first or last pit measurement",
        ["Time start/end", "time_start/end"]
    )

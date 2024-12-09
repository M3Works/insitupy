import inspect
import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict


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
    auto_remap: bool = False  # Auto remap to the column to the code
    match_on_code: bool = True  # Match on the code too
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

    @classmethod
    def from_mapping(
        cls, input_name, allow_failure=False
    ) -> Tuple[str, Dict[str, MeasurementDescription]]:
        """
        Get the measurement description from an input name.
        This will use the  MeasurementDescription.map_from list to
        check, in order, which variable we should use

        Args:
            input_name: string input name
            allow_failure: return the original name if we fail

        Returns:
            column name
            column mapping (map of name to MeasurementDescription)
        """
        lower_name = input_name.lower()
        result = None
        # Map column name to variable type
        column_mapping = {}
        for entry in cls():
            # Check if we match directly on the code
            code_match = entry.match_on_code and lower_name == entry.code
            # Check if we match from the list of possible matches
            map_match = entry.map_from and lower_name in entry.map_from
            if code_match or map_match:
                # Remap to code
                if entry.auto_remap:
                    result = entry.code
                else:
                    result = input_name
                # store a map of the column name to the variable description
                column_mapping[result] = entry
                break
        if result is None:
            if allow_failure:
                # We failed to find a mapping, but want to continue
                LOG.warning(f"Could not find mapping for {input_name}")
                result = input_name
                column_mapping[result] = None
            else:
                raise RuntimeError(f"Could not find mapping for {input_name}")
        LOG.debug(
            f"Mapping {result} to {result} (type {column_mapping[result]})"
        )
        return result, column_mapping

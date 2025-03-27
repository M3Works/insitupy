import inspect
import logging
import os.path
from dataclasses import dataclass
from typing import List, Tuple, Dict
import attrs
import pydash
import yaml

LOG = logging.getLogger(__name__)


# Similar to MeasurementDescription from metloom
@attrs.frozen
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


def variable_from_input(x):
    """
    Get all the variables from a set of files
    Args:
        x: input

    Returns:
        list of variables
    """
    if isinstance(x, list) and all(os.path.isfile(f) for f in x):
        data_final = {}
        # If we have a list of files, we need to import them
        for f in x:
            with open(f) as fp:
                data = yaml.safe_load(fp)
            # Merge, overwriting options with second
            pydash.merge(data_final, data)
        return {k: MeasurementDescription(**v) for k, v in data_final.items()}
    # Assume properly formatted list
    return x


@attrs.define
class ExtendableVariables:
    """
    Make a class with the helpful iterator for storing variable options
    """
    entries: dict[str, MeasurementDescription] = attrs.field(
        factory=dict,
        converter=attrs.Converter(variable_from_input)
    )

    @property
    def variables(self):
        return list(self.entries.values())

    @property
    def keys(self):
        return list(self.entries.keys())

    def __iter__(self):
        for item in self.variables:
            yield item

    def __len__(self):
        return len(self.entries)

    def from_mapping(
        self, input_name, allow_failure=False
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
        for entry in self.variables:
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

    def to_dict(self):
        return {k: attrs.asdict(v) for k, v in self.entries.items()}

    def to_yaml(self, output_file):
        with open(output_file, 'w') as fp:
            data = self.to_dict()
            yaml.dump(data, fp)

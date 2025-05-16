import logging
import os.path
from pathlib import Path
from typing import Dict, List, Tuple, Union

import attrs
import pydash
import yaml
from attrs import field, validators

LOG = logging.getLogger(__name__)


class InputMappingError(RuntimeError):
    """
    Indicate we failed to map a column or header name
    """
    pass


# Similar to MeasurementDescription from metloom
@attrs.frozen
class MeasurementDescription:
    """
    data class for describing a measurement

    Args:
        code: code used within the applicable API
        description: description of the sensor
        map_from: List map to this variable from a list of options
        auto_remap: Auto remap to the column to the code
        match_on_code: Match on the code too
        cast_type: make this float, int, etc
    """
    # Code used within the applicable API
    code: str = field(default='-1', validator=validators.instance_of(str))
    # Description of the measurement
    description: str = None
    # Map to this variable from a list of options
    map_from: List = field(
        default=[],
        validator=attrs.validators.optional(validators.instance_of(List))
    )
    # Auto remap the column to the code
    auto_remap: bool = False
    # Match on the code too
    match_on_code: bool = True
    # Optional value type casting
    cast_type: str = None


def variable_from_input(files: list[Union[str, Path]], self_):
    """
    Parses list of YAML files that have primary or metadata variable
    definitions.

    Args:
        files (list[Union[str, Path]] | dict): List of files to parse.
        self_: The instance of the initialized ExtendableVariables class.

    Returns:
        dict: A dictionary with parsed MeasurementDescription objects.

    Raises:
        TypeError: If the input `x` is neither a list of files nor a valid
        dictionary.
    """
    # TODO: better logic here
    if isinstance(files, list) and all(os.path.isfile(f) for f in files):
        data_final = {}
        # If we have a list of files, we need to import them
        for f in files:
            self_.source_files = self_.source_files + [str(f)]
            with open(f) as fp:
                data = yaml.safe_load(fp)
            # Merge, overwriting options with second
            pydash.merge(data_final, data)
        return {k: MeasurementDescription(**v) for k, v in data_final.items()}
    # Check that we have a dict
    if not isinstance(files, dict):
        raise TypeError(
            f"Expected to formulate dict, got {type(files)} with value {files}"
        )
    return files


@attrs.define
class ExtendableVariables:
    """
    Make a class with the helpful iterator for storing variable options
    """
    source_files: list[str] = []
    entries: dict[str, MeasurementDescription] = attrs.field(
        factory=dict,
        converter=attrs.Converter(variable_from_input, takes_self=True)
    )
    allow_map_failures: bool = False

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
        self, input_name
    ) -> Tuple[str, Dict[str, MeasurementDescription]]:
        """
        Get the measurement description from an input name.
        This will use the MeasurementDescription.map_from list to
        check, in order, which variable we should use

        Args:
            input_name: string input name

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
            if self.allow_map_failures:
                # We failed to find a mapping, but want to continue
                LOG.warning(f"Could not find mapping for {input_name}")
                result = input_name
                column_mapping[result] = None
            else:
                raise InputMappingError(
                    f"Could not find mapping for {input_name}"
                )
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

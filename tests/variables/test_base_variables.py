# tests/test_base_variables.py

import pytest

from insitupy.variables import ExtendableVariables, MeasurementDescription, \
    base_primary_variables_yaml
from insitupy.variables.base_variables import InputMappingError


@pytest.fixture
def sample_entries():
    return {
        "TEMP": MeasurementDescription(
            code="TEMP",
            description="Temperature measurement",
            map_from=["temperature", "temp"],
            auto_remap=True,
            match_on_code=True
        ),
        "DENSITY": MeasurementDescription(
            code="DENSITY",
            description="Density measurement",
            map_from=["density"],
            auto_remap=False,
            match_on_code=True
        )
    }


@pytest.fixture
def extendable_variables_fixture(sample_entries):
    return ExtendableVariables(entries=sample_entries)


class TestExtendableVariables:
    def test_variables_property(
        self, extendable_variables_fixture, sample_entries
    ):
        assert extendable_variables_fixture.variables == list(
            sample_entries.values()
        )

    def test_keys_property(
        self, extendable_variables_fixture, sample_entries
    ):
        assert extendable_variables_fixture.keys == list(sample_entries.keys())

    def test_iteration_over_variables(
        self, extendable_variables_fixture, sample_entries
    ):
        for i, variable in enumerate(extendable_variables_fixture):
            assert variable == list(sample_entries.values())[i]

    def test_length_of_entries(
        self, extendable_variables_fixture, sample_entries
    ):
        assert len(extendable_variables_fixture) == len(sample_entries)

    def test_from_mapping_success_on_code(
        self, extendable_variables_fixture
    ):
        result, mapping = extendable_variables_fixture.from_mapping("temp")
        assert result == "TEMP"
        assert result in mapping
        assert mapping[result].description == "Temperature measurement"

    def test_from_mapping_failure(self, extendable_variables_fixture):
        with pytest.raises(
                InputMappingError, match="Could not find mapping for humidity"
        ):
            extendable_variables_fixture.from_mapping("humidity")

    def test_from_mapping_allow_failures(self):
        ev = ExtendableVariables(entries={}, allow_map_failures=True)
        result, mapping = ev.from_mapping("unknown_variable")
        assert result == "unknown_variable"
        assert mapping[result] is None

    def test_source_files(self, tmp_path):
        overwrites = tmp_path / "overwrites.yaml"
        overwrites.write_text("TEMP:\n  description: Overwritten description")
        ev = ExtendableVariables(
            entries=[base_primary_variables_yaml, overwrites],
            allow_map_failures=True
        )
        assert len(ev.source_files) == 2
        assert str(overwrites) in ev.source_files
        assert str(base_primary_variables_yaml) in ev.source_files

        # Make sure we properly append the file entries to the list of files
        # and don't maintain old entries between new object instances
        overwrites = tmp_path / "overwrites_2.yaml"
        overwrites.write_text("TEMP:\n  description: Overwritten description")
        ev = ExtendableVariables(
            entries=[overwrites],
            allow_map_failures=True
        )
        assert len(ev.source_files) == 1
        assert ev.source_files == [str(overwrites)]

    def test_to_dict(self, extendable_variables_fixture):
        result = extendable_variables_fixture.to_dict()
        assert isinstance(result, dict)
        assert "TEMP" in result
        assert result["TEMP"]["description"] == "Temperature measurement"

    def test_to_yaml(self, extendable_variables_fixture, tmp_path):
        yaml_file = tmp_path / "output.yaml"
        extendable_variables_fixture.to_yaml(yaml_file)
        assert yaml_file.exists()
        with open(yaml_file, "r") as f:
            content = f.read()
            assert "TEMP" in content
            assert "description: Temperature measurement" in content


class TestMeasurementDescription:
    @pytest.mark.parametrize(
        "code, description, map_from, auto_remap, match_on_code, cast_type",
        [
            ("AIR_TEMP", "Temperature", ["temp", "temperature"],
             True, True, "int"),
            ("", None, [], False, True, None),
            ("PRESS", "Pressure", ["pressure"], False, False, "float"),
        ],
    )
    def test_initialization(
        self, code, description, map_from, auto_remap, match_on_code, cast_type
    ):
        measurement = MeasurementDescription(
            code=code,
            description=description,
            map_from=map_from,
            auto_remap=auto_remap,
            match_on_code=match_on_code,
            cast_type=cast_type,
        )
        assert measurement.code == code
        assert measurement.description == description
        assert measurement.map_from == map_from
        assert measurement.auto_remap == auto_remap
        assert measurement.match_on_code == match_on_code
        assert measurement.cast_type == cast_type

    def test_default_values(self):
        measurement = MeasurementDescription()
        assert measurement.code == "-1"
        assert measurement.description is None
        assert measurement.map_from == []
        assert not measurement.auto_remap
        assert measurement.match_on_code
        assert measurement.cast_type is None

    def test_invalid_code_type(self):
        with pytest.raises(TypeError):
            MeasurementDescription(code=123)

    def test_invalid_map_from_type(self):
        with pytest.raises(TypeError):
            MeasurementDescription(map_from="not a list")

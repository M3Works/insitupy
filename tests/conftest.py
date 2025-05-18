from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def data_path():
    return Path(__file__).parent.joinpath(
        "data/snowex/pits/"
    ).expanduser().absolute()


@pytest.fixture
def yaml_variable_file(tmp_path):
    """
    Create temporary yaml files for metadata or primary variables

    Yields:
        Function to create file
    """
    def _create_yaml_file(filename: str, variable_name: str = 'VAR_1'):
        file = tmp_path / filename
        file.write_text(
            f"{variable_name}:\n  description: Variable description"
        )
        return file

    yield _create_yaml_file

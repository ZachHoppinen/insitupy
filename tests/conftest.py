import pytest
from pathlib import Path


@pytest.fixture(scope="module")
def data_path():
    return Path(__file__).parent.joinpath(
        "data/pits/"
    ).expanduser().absolute()

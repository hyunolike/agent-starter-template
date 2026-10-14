import pytest
from fastapi.testclient import TestClient

from agent_app.config import Settings
from agent_app.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, database_path=tmp_path / "test.sqlite", model_provider="demo")


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client

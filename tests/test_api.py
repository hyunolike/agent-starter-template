import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import ToolMessage
from pydantic import SecretStr

from agent_app.integrations.model import DemoModel
from agent_app.main import create_app


def test_health_and_calculation(client):
    assert client.get("/healthz").json() == {"status": "ok", "model_provider": "demo"}
    result = client.post("/v1/runs", json={"message": "12 * 7"}).json()
    assert result["status"] == "completed"
    assert '"result": 84.0' in result["output"]
    assert result["tool_events"] == [{"name": "calculate", "error": None}]
    assert result["model_calls"] == 2
    assert result["input_tokens"] == 0


@pytest.mark.parametrize("message", ["", "   ", "x" * 4001])
def test_invalid_messages(client, message):
    assert client.post("/v1/runs", json={"message": message}).status_code == 422


def test_unknown_fields_and_invalid_thread(client):
    assert client.post("/v1/runs", json={"message": "hi", "model": "override"}).status_code == 422
    assert client.post("/v1/runs", json={"message": "hi", "thread_id": "../x"}).status_code == 422
    assert client.get(f"/v1/threads/{uuid4()}").status_code == 404


def test_auth_protects_all_agent_routes(settings):
    settings.api_token = SecretStr("test-token")
    with TestClient(create_app(settings)) as client:
        assert client.get("/healthz").status_code == 200
        assert client.post("/v1/runs", json={"message": "MFA"}).status_code == 401
        assert client.get(f"/v1/threads/{uuid4()}").status_code == 401
        assert client.post(f"/v1/threads/{uuid4()}/resume").status_code == 401
        result = client.post(
            "/v1/runs", json={"message": "MFA"}, headers={"Authorization": "Bearer test-token"}
        )
        assert result.status_code == 200


def test_conversation_persists_across_app_restarts(settings):
    with TestClient(create_app(settings)) as client:
        result = client.post("/v1/runs", json={"message": "REQ-1001"}).json()
        thread = result["thread_id"]
    with TestClient(create_app(settings)) as client:
        response = client.post("/v1/runs", json={"message": "history", "thread_id": thread})
        assert "REQ-1001" in response.json()["output"]
        other = client.post("/v1/runs", json={"message": "history"}).json()
        assert "REQ-1001" not in other["output"]
        assert client.post(f"/v1/threads/{thread}/resume").status_code == 409


def test_history_limit(settings):
    settings.max_history_messages = 10
    with TestClient(create_app(settings)) as client:
        thread = str(uuid4())
        for _ in range(3):
            assert (
                client.post("/v1/runs", json={"message": "MFA", "thread_id": thread}).status_code
                == 200
            )
        response = client.post("/v1/runs", json={"message": "MFA", "thread_id": thread})
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "history_limit_reached"


def test_sqlite_resume_after_timeout_and_restart(settings):
    class SlowSummary(DemoModel):
        async def ainvoke(self, messages):
            if isinstance(messages[-1], ToolMessage):
                await asyncio.sleep(2)
            return await super().ainvoke(messages)

    settings.run_timeout_seconds = 0.2
    with TestClient(create_app(settings, model=SlowSummary())) as client:
        response = client.post("/v1/runs", json={"message": "12 * 7"})
        assert response.status_code == 504
        thread = response.json()["detail"]["thread_id"]
        assert client.get(f"/v1/threads/{thread}").json()["pending"] is True

    settings.run_timeout_seconds = 2
    with TestClient(create_app(settings)) as client:
        result = client.post(f"/v1/threads/{thread}/resume").json()
        assert result["status"] == "completed"
        assert "84.0" in result["output"]
        assert result["tool_calls"] == 1
        assert len(result["tool_events"]) == 1

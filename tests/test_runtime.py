import asyncio
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from agent_app.agent.graph import build_graph
from agent_app.integrations.model import DemoModel, build_model
from agent_app.services.runtime import AgentRuntime, RuntimeErrorResponse
from agent_app.tools.registry import build_tools


class LoopModel:
    async def ainvoke(self, messages):
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "id": str(uuid4()),
                    "name": "calculate",
                    "type": "tool_call",
                    "args": {"operation": "add", "a": 1, "b": 1},
                }
            ],
        )


def runtime(settings, model):
    return AgentRuntime(build_graph(settings, model, build_tools(), InMemorySaver()), settings)


async def test_model_call_budget(settings):
    settings.max_model_calls = 2
    result = await runtime(settings, LoopModel()).run("loop")
    assert result.status == "limit_reached"
    assert result.model_calls == 2


async def test_tool_call_budget(settings):
    settings.max_tool_calls = 1
    result = await runtime(settings, LoopModel()).run("loop")
    assert result.status == "limit_reached"
    assert result.tool_calls == 1
    assert result.tool_events[-1].error == "tool_call_limit_reached"


async def test_model_error_is_safe(settings):
    class Broken:
        async def ainvoke(self, messages):
            raise RuntimeError("secret-provider-response")

    result = await runtime(settings, Broken()).run("hello")
    assert result.status == "model_error"
    assert "secret" not in result.output


async def test_same_thread_conflict(settings):
    entered, release = asyncio.Event(), asyncio.Event()

    class Waiting(DemoModel):
        async def ainvoke(self, messages):
            entered.set()
            await release.wait()
            return await super().ainvoke(messages)

    runner = runtime(settings, Waiting())
    thread = str(uuid4())
    task = asyncio.create_task(runner.run("MFA", thread))
    await asyncio.wait_for(entered.wait(), 2)
    try:
        with pytest.raises(RuntimeErrorResponse) as exc:
            await runner.run("MFA", thread)
        assert exc.value.code == "thread_busy"
    finally:
        release.set()
        await task
    assert not runner.active_threads


async def test_timeout_can_resume_and_keeps_budget(settings):
    class SlowOnce(DemoModel):
        first = True

        async def ainvoke(self, messages):
            if self.first:
                self.first = False
                await asyncio.sleep(2)
            return await super().ainvoke(messages)

    settings.run_timeout_seconds = 0.1
    runner = runtime(settings, SlowOnce())
    thread = str(uuid4())
    with pytest.raises(RuntimeErrorResponse) as exc:
        await runner.run("12 * 7", thread)
    assert exc.value.code == "run_timeout"
    assert (await runner.inspect(thread)).pending is True
    with pytest.raises(RuntimeErrorResponse) as conflict:
        await runner.run("new message", thread)
    assert conflict.value.code == "resume_required"
    settings.run_timeout_seconds = 2
    result = await runner.run(None, thread)
    assert result.status == "completed"
    assert result.tool_calls == 1


def test_real_model_adapter_binds_without_network(settings, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    settings.model_provider = "anthropic"
    model = build_model(settings, build_tools())
    assert len(model.kwargs["tools"]) == 3

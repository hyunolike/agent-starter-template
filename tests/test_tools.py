import asyncio

import pytest
from langchain_core.tools import StructuredTool

from agent_app.policies.tool_access import execute_tool
from agent_app.tools.registry import SearchInput, build_tools


@pytest.fixture
def registry():
    return {tool.name: tool for tool in build_tools()}


async def test_calculator_validates_and_handles_zero(registry):
    assert await execute_tool(
        "calculate", {"operation": "divide", "a": 10, "b": 2}, registry, 1
    ) == {"result": 5}
    assert await execute_tool(
        "calculate", {"operation": "divide", "a": 1, "b": 0}, registry, 1
    ) == {"error": "division_by_zero"}
    for args in [
        {"operation": "eval", "a": 1, "b": 2},
        {"operation": "add", "a": float("inf"), "b": 1},
        {"operation": "add", "a": 1, "b": 2, "code": "print('unsafe')"},
    ]:
        assert (await execute_tool("calculate", args, registry, 1))[
            "error"
        ] == "invalid_tool_arguments"


async def test_tool_allowlist(registry):
    assert await execute_tool("delete_everything", {}, registry, 1) == {"error": "tool_not_allowed"}


async def test_no_evidence_and_missing_request(registry):
    result = await execute_tool("search_documents", {"query": "unobtainium"}, registry, 1)
    assert result["matches"] == []
    result = await execute_tool("get_request_status", {"request_id": "REQ-9999"}, registry, 1)
    assert result["found"] is False
    assert result["data"] is None


async def test_tool_timeout_and_error_redaction():
    async def slow(query: str, limit: int = 3):
        await asyncio.sleep(1)

    async def broken(query: str, limit: int = 3):
        raise RuntimeError("secret-value-must-not-leak")

    for fn, expected in [(slow, "tool_timeout"), (broken, "tool_execution_failed")]:
        tool = StructuredTool.from_function(
            coroutine=fn, name="test", description="Test tool", args_schema=SearchInput
        )
        result = await execute_tool("test", {"query": "x"}, {"test": tool}, 0.01)
        assert result == {"error": expected}

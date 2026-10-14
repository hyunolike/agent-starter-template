import operator
from typing import Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from agent_app.services.knowledge import search_knowledge
from agent_app.services.requests import get_request


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchInput(ToolInput):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=3, ge=1, le=5)


class RequestInput(ToolInput):
    request_id: str = Field(pattern=r"^REQ-\d{4}$")


class CalculateInput(ToolInput):
    operation: Literal["add", "subtract", "multiply", "divide"]
    a: float = Field(ge=-1e12, le=1e12, allow_inf_nan=False)
    b: float = Field(ge=-1e12, le=1e12, allow_inf_nan=False)


async def search_documents(query: str, limit: int = 3) -> dict:
    return search_knowledge(query, limit)


async def get_request_status(request_id: str) -> dict:
    return get_request(request_id)


async def calculate(operation: str, a: float, b: float) -> dict:
    operations = {
        "add": operator.add,
        "subtract": operator.sub,
        "multiply": operator.mul,
        "divide": operator.truediv,
    }
    if operation == "divide" and b == 0:
        return {"error": "division_by_zero"}
    return {"result": operations[operation](a, b)}


def build_tools() -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            coroutine=search_documents,
            name="search_documents",
            description="Search fictional demo policies by keyword. Return sources; no matches "
            "means no evidence. Not a web or semantic search.",
            args_schema=SearchInput,
        ),
        StructuredTool.from_function(
            coroutine=get_request_status,
            name="get_request_status",
            description="Read a fictional request status using an exact REQ-1234 identifier.",
            args_schema=RequestInput,
        ),
        StructuredTool.from_function(
            coroutine=calculate,
            name="calculate",
            description="Perform one arithmetic operation on two finite numbers.",
            args_schema=CalculateInput,
        ),
    ]

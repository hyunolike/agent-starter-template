from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from agent_app.agent.state import RunStatus


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    thread_id: UUID | None = None


class ToolEvent(BaseModel):
    name: str
    error: str | None = None


class RunResponse(BaseModel):
    run_id: str
    thread_id: str
    status: RunStatus
    output: str
    model_provider: str
    model_calls: int
    tool_calls: int
    tool_events: list[ToolEvent]
    input_tokens: int
    output_tokens: int


class ThreadResponse(BaseModel):
    thread_id: str
    pending: bool
    status: str
    message_count: int = Field(ge=0)

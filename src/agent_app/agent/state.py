from typing import Literal

from langgraph.graph import MessagesState

RunStatus = Literal["running", "completed", "limit_reached", "model_error"]


class AgentState(MessagesState):
    model_calls: int
    tool_calls: int
    tool_events: list[dict]
    status: RunStatus
    input_tokens: int
    output_tokens: int

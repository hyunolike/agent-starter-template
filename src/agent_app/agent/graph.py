import json
import logging
from importlib.resources import files

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from agent_app.agent.state import AgentState
from agent_app.config import Settings
from agent_app.integrations.model import AgentModel
from agent_app.policies.tool_access import execute_tool

logger = logging.getLogger(__name__)


def build_graph(settings: Settings, model: AgentModel, tools: list, checkpointer):
    registry = {tool.name: tool for tool in tools}
    instructions = (
        files("agent_app").joinpath("agent/prompts/system.md").read_text(encoding="utf-8")
    )

    async def call_model(state: AgentState):
        if state["model_calls"] >= settings.max_model_calls:
            return {
                "messages": [AIMessage(content="Stopped: model-call limit reached.")],
                "status": "limit_reached",
            }
        try:
            response = await model.ainvoke(
                [SystemMessage(content=instructions), *state["messages"]]
            )
            if not isinstance(response, AIMessage):
                raise TypeError("Expected AIMessage")
            if response.invalid_tool_calls:
                raise ValueError("Malformed tool calls")
        except Exception:
            logger.warning("model_call_failed", extra={"event": "model_call_failed"})
            return {
                "messages": [AIMessage(content="The model could not complete this request.")],
                "model_calls": state["model_calls"] + 1,
                "status": "model_error",
            }
        usage = response.usage_metadata or {}
        return {
            "messages": [response],
            "model_calls": state["model_calls"] + 1,
            "input_tokens": state["input_tokens"] + usage.get("input_tokens", 0),
            "output_tokens": state["output_tokens"] + usage.get("output_tokens", 0),
            "status": "running" if response.tool_calls else "completed",
        }

    async def call_tools(state: AgentState):
        messages, events = [], list(state["tool_events"])
        count = state["tool_calls"]
        exhausted = False
        for call in state["messages"][-1].tool_calls:
            if count >= settings.max_tool_calls:
                result = {"error": "tool_call_limit_reached"}
                exhausted = True
            else:
                count += 1
                result = await execute_tool(
                    call["name"], call["args"], registry, settings.tool_timeout_seconds
                )
            messages.append(
                ToolMessage(content=json.dumps(result, ensure_ascii=False), tool_call_id=call["id"])
            )
            events.append({"name": call["name"], "error": result.get("error")})
        if exhausted:
            messages.append(AIMessage(content="Stopped: tool-call limit reached."))
        return {
            "messages": messages,
            "tool_calls": count,
            "tool_events": events,
            "status": "limit_reached" if exhausted else "running",
        }

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", call_tools)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent", lambda state: "tools" if state["status"] == "running" else END
    )
    graph.add_conditional_edges(
        "tools", lambda state: "agent" if state["status"] == "running" else END
    )
    return graph.compile(checkpointer=checkpointer)

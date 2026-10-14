import json
import re
from typing import Protocol
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool

from agent_app.config import Settings


class AgentModel(Protocol):
    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage: ...


class DemoModel:
    """A deterministic scripted adapter, NOT a language model or quality benchmark."""

    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        last = messages[-1]
        if isinstance(last, ToolMessage):
            return AIMessage(content=f"Demo tool result: {last.content}")
        text = str(last.content).strip()
        if text.lower() == "history":
            prior = [str(m.content) for m in messages[:-1] if isinstance(m, HumanMessage)]
            return AIMessage(content=json.dumps({"previous_user_messages": prior}))
        arithmetic = re.fullmatch(
            r"(?:calculate\s+)?(-?\d+(?:\.\d+)?)\s*([+*/-])\s*(-?\d+(?:\.\d+)?)", text
        )
        request = re.search(r"\bREQ-\d{4}\b", text.upper())
        if arithmetic:
            a, symbol, b = arithmetic.groups()
            name = "calculate"
            args = {
                "operation": {"+": "add", "-": "subtract", "*": "multiply", "/": "divide"}[symbol],
                "a": float(a),
                "b": float(b),
            }
        elif request:
            name, args = "get_request_status", {"request_id": request.group()}
        else:
            name, args = "search_documents", {"query": text[:500]}
        return AIMessage(
            content="",
            tool_calls=[{"name": name, "args": args, "id": str(uuid4()), "type": "tool_call"}],
        )


def build_model(settings: Settings, tools: list[BaseTool]) -> AgentModel:
    if settings.model_provider == "demo":
        return DemoModel()
    from langchain_anthropic import ChatAnthropic

    # The provider reads ANTHROPIC_API_KEY from the environment.
    return ChatAnthropic(
        model_name=settings.model_name,
        max_tokens_to_sample=1024,
        temperature=0,
        timeout=settings.run_timeout_seconds,
        max_retries=1,
    ).bind_tools(tools)

import asyncio
import logging

from langchain_core.tools import BaseTool
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def execute_tool(name: str, arguments: dict, registry: dict[str, BaseTool], seconds: float):
    tool = registry.get(name)
    if tool is None:
        return {"error": "tool_not_allowed"}
    try:
        async with asyncio.timeout(seconds):
            return await tool.ainvoke(arguments)
    except ValidationError:
        return {"error": "invalid_tool_arguments"}
    except TimeoutError:
        return {"error": "tool_timeout"}
    except Exception:
        # Do not put upstream exception messages, credentials, or tool inputs in logs.
        logger.warning("tool_execution_failed", extra={"event": "tool_execution_failed"})
        return {"error": "tool_execution_failed"}

import asyncio
import logging
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage

from agent_app.api.schemas import RunResponse, ThreadResponse
from agent_app.config import Settings

logger = logging.getLogger(__name__)


class RuntimeErrorResponse(Exception):
    def __init__(self, code: str, status_code: int, thread_id: str):
        self.code, self.status_code, self.thread_id = code, status_code, thread_id


class AgentRuntime:
    """Single-process coordinator. No distributed locking or exactly-once claims."""

    def __init__(self, graph, settings: Settings):
        self.graph, self.settings = graph, settings
        self.active_threads: set[str] = set()

    def config(self, thread_id: str) -> dict:
        return {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": self.settings.max_model_calls * 2 + 4,
        }

    async def inspect(self, thread_id: str) -> ThreadResponse:
        snapshot = await self.graph.aget_state(self.config(thread_id))
        if not snapshot.values:
            raise RuntimeErrorResponse("thread_not_found", 404, thread_id)
        return ThreadResponse(
            thread_id=thread_id,
            pending=bool(snapshot.next),
            status=snapshot.values.get("status", "running"),
            message_count=len(snapshot.values.get("messages", [])),
        )

    async def run(self, message: str | None, thread_id: str | None = None) -> RunResponse:
        thread_id, run_id = thread_id or str(uuid4()), str(uuid4())
        if thread_id in self.active_threads:
            raise RuntimeErrorResponse("thread_busy", 409, thread_id)
        # No await between the membership check and add: atomic within this event loop.
        self.active_threads.add(thread_id)
        try:
            config = self.config(thread_id)
            snapshot = await self.graph.aget_state(config)
            if message is None:
                if not snapshot.values:
                    raise RuntimeErrorResponse("thread_not_found", 404, thread_id)
                if not snapshot.next:
                    raise RuntimeErrorResponse("nothing_to_resume", 409, thread_id)
                inputs = None
            else:
                if snapshot.next:
                    raise RuntimeErrorResponse("resume_required", 409, thread_id)
                if len(snapshot.values.get("messages", [])) >= self.settings.max_history_messages:
                    raise RuntimeErrorResponse("history_limit_reached", 409, thread_id)
                inputs = {
                    "messages": [HumanMessage(content=message)],
                    "model_calls": 0,
                    "tool_calls": 0,
                    "tool_events": [],
                    "status": "running",
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            try:
                async with asyncio.timeout(self.settings.run_timeout_seconds):
                    result = await self.graph.ainvoke(inputs, config)
            except TimeoutError as exc:
                raise RuntimeErrorResponse("run_timeout", 504, thread_id) from exc
            final = result["messages"][-1]
            output = final.text if isinstance(final, AIMessage) else str(final.content)
            response = RunResponse(
                run_id=run_id,
                thread_id=thread_id,
                status=result["status"],
                output=output,
                model_provider=self.settings.model_provider,
                model_calls=result["model_calls"],
                tool_calls=result["tool_calls"],
                tool_events=result["tool_events"],
                input_tokens=result["input_tokens"],
                output_tokens=result["output_tokens"],
            )
            logger.info(
                "run_finished",
                extra={"event": "run_finished", "run_id": run_id, "status": result["status"]},
            )
            return response
        finally:
            self.active_threads.discard(thread_id)

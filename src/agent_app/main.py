from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agent_app.agent.graph import build_graph
from agent_app.api.routes import router
from agent_app.config import Settings
from agent_app.integrations.model import build_model
from agent_app.observability.logging import configure_logging
from agent_app.persistence.checkpoints import open_checkpointer
from agent_app.services.runtime import AgentRuntime, RuntimeErrorResponse
from agent_app.tools.registry import build_tools


def create_app(settings: Settings | None = None, model=None) -> FastAPI:
    load_dotenv(override=False)
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        tools = build_tools()
        chosen_model = model if model is not None else build_model(settings, tools)
        async with open_checkpointer(settings.database_path) as saver:
            app.state.settings = settings
            app.state.runtime = AgentRuntime(
                build_graph(settings, chosen_model, tools, saver), settings
            )
            yield

    app = FastAPI(
        title="Agent Starter Template",
        description="A single-tenant, read-only agent sandbox. Demo mode needs no API key.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.exception_handler(RuntimeErrorResponse)
    async def runtime_error(request: Request, exc: RuntimeErrorResponse):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"code": exc.code, "thread_id": exc.thread_id}},
        )

    @app.get("/healthz", tags=["health"])
    async def health():
        return {"status": "ok", "model_provider": settings.model_provider}

    app.include_router(router)
    return app

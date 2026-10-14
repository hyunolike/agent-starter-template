import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from agent_app.api.schemas import RunRequest, RunResponse, ThreadResponse

bearer = HTTPBearer(auto_error=False)


def authorize(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> None:
    expected = request.app.state.settings.api_token.get_secret_value()
    if expected and (
        credentials is None
        or not secrets.compare_digest(credentials.credentials.encode(), expected.encode())
    ):
        raise HTTPException(401, "Invalid bearer token", headers={"WWW-Authenticate": "Bearer"})


router = APIRouter(prefix="/v1", dependencies=[Depends(authorize)])


@router.post("/runs", response_model=RunResponse)
async def run_agent(body: RunRequest, request: Request):
    return await request.app.state.runtime.run(
        body.message, str(body.thread_id) if body.thread_id else None
    )


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def inspect_thread(thread_id: UUID, request: Request):
    return await request.app.state.runtime.inspect(str(thread_id))


@router.post("/threads/{thread_id}/resume", response_model=RunResponse)
async def resume_thread(thread_id: UUID, request: Request):
    return await request.app.state.runtime.run(None, str(thread_id))

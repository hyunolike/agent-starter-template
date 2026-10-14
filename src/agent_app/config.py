from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENT_", env_file=".env", extra="ignore")

    model_provider: Literal["demo", "anthropic"] = "demo"
    model_name: str = "claude-sonnet-4-6"
    api_token: SecretStr = SecretStr("")
    database_path: Path = Path("var/checkpoints.sqlite")
    max_model_calls: int = Field(default=5, ge=1, le=50)
    max_tool_calls: int = Field(default=8, ge=1, le=100)
    run_timeout_seconds: float = Field(default=60, gt=0, le=600)
    tool_timeout_seconds: float = Field(default=10, gt=0, le=60)
    max_history_messages: int = Field(default=200, ge=10, le=1000)

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file (not CWD) so it works whether uvicorn/pytest
# is launched from the repo root or from backend/, per the documented dev flow.
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), str(_BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"

    database_url: str = "postgresql+psycopg://policylens:policylens@localhost:5432/policylens"
    database_url_test: str = (
        "postgresql+psycopg://policylens:policylens@localhost:5432/policylens_test"
    )

    demo_username: str = "demo"
    demo_password_hash: str = ""
    auth_secret: str = "insecure-dev-secret-change-me"
    auth_token_ttl_minutes: int = 720

    documents_dir: str = "data/documents"
    markdown_dir: str = "data/markdown"
    chroma_dir: str = "data/chroma"

    openai_api_key: str = ""
    chat_model: str = "gpt-5.4-mini"
    embedding_model: str = "text-embedding-3-small"

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "policylens"

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def _resolve(self, value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        return path.resolve()

    @property
    def documents_dir_path(self) -> Path:
        return self._resolve(self.documents_dir)

    @property
    def markdown_dir_path(self) -> Path:
        return self._resolve(self.markdown_dir)

    @property
    def chroma_dir_path(self) -> Path:
        return self._resolve(self.chroma_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# `langsmith.traceable` decorators check LANGSMITH_TRACING in os.environ at *decoration*
# time (when a decorated module is first imported), not at call time - setting these
# later, e.g. lazily inside a request handler, is too late and silently no-ops tracing
# for the rest of the process. This module is imported before any `@traceable`-decorated
# code (everything does `from app.config import get_settings`), so it's the earliest
# reliable place to push these into the real environment.
_settings = get_settings()
if _settings.langsmith_tracing and _settings.langsmith_api_key:
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", _settings.langsmith_api_key)
    os.environ.setdefault("LANGSMITH_PROJECT", _settings.langsmith_project)

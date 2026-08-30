"""Raw OpenAI SDK client - used only by app/rag/embeddings.py for offline ingestion.
The live agent (app/rag/agent.py) goes through LangChain's ChatOpenAI instead, which
LangSmith traces automatically; there's nothing to wrap here."""

from functools import lru_cache

from openai import OpenAI

from app.config import get_settings


@lru_cache
def get_openai_client() -> OpenAI:
    return OpenAI(api_key=get_settings().openai_api_key)

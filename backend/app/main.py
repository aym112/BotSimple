from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import auth, documents, health, query, traces
from app.config import get_settings
from app.rate_limit import limiter

settings = get_settings()


def _ensure_corpus_ingested() -> None:
    """Some free hosting tiers (e.g. Render's free web service) wipe local disk on
    every cold start, which would otherwise lose the Markdown files and Chroma
    embeddings. The corpus is fixed and small, so re-ingesting on an empty store is
    cheap - this makes the app work on ephemeral storage without a persistent volume."""
    from app.rag.vectorstore import get_collection

    if get_collection().count() > 0:
        return

    from app.ingestion.cli import ingest_directory

    print("Corpus store is empty - running ingestion before accepting requests...")
    ingest_directory(settings.documents_dir_path)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _ensure_corpus_ingested()
    yield


app = FastAPI(title="AymanChat API", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # pyright: ignore[reportArgumentType]
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(query.router)
app.include_router(traces.router)
app.include_router(documents.router)

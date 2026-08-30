"""Chroma is the vector store: local, embedded, persisted to a directory on disk -
no server to run or deploy, which is what keeps this stack simple to ship."""

from functools import lru_cache

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from app.config import get_settings

_COLLECTION_NAME = "policylens_documents"


@lru_cache
def _get_client() -> ClientAPI:
    chroma_dir = get_settings().chroma_dir_path
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(chroma_dir))


def get_collection() -> Collection:
    return _get_client().get_or_create_collection(_COLLECTION_NAME)


def reset_collection() -> Collection:
    client = _get_client()
    try:
        client.delete_collection(_COLLECTION_NAME)
    except Exception:
        pass
    return client.get_or_create_collection(_COLLECTION_NAME)

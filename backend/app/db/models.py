"""SQLAlchemy models.

Retrieval no longer goes through Postgres — the agent searches a Chroma vector store
and greps Markdown files on disk (see app/rag/). `documents` stays as the metadata
table backing the corpus browser, PDF serving and citations; `query_requests` logs
each agent turn for the /requests endpoints.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    product: Mapped[str | None] = mapped_column(String(64), nullable=True)
    authority: Mapped[str] = mapped_column(String(16), nullable=False, default="contractual")
    contractual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class QueryRequest(Base):
    """Logs one agent turn - backs the /requests/{id} and /requests/{id}/trace endpoints."""

    __tablename__ = "query_requests"

    id: Mapped[uuid.UUID] = _uuid_pk()
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tool_calls_json: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

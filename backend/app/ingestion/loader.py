"""Ingest one PDF: parse it, write a Markdown copy to disk (the agent's grep target),
embed its chunks into Chroma (the agent's semantic search target), and upsert a
`Document` metadata row (corpus browser, PDF serving, citations)."""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from chromadb.api.types import PyEmbeddings
from sqlalchemy.orm import Session

from app.db.models import Document
from app.ingestion.markdown_writer import write_markdown
from app.ingestion.metadata import extract_document_metadata
from app.ingestion.pdf_parser import parse_pdf
from app.rag.chunking import build_chunks
from app.rag.embeddings import embed_texts
from app.rag.vectorstore import get_collection


@dataclass
class IngestResult:
    filename: str
    document_id: str
    chunks: int
    markdown_path: str


def ingest_document(session: Session, path: Path, markdown_dir: Path) -> IngestResult:
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    parsed = parse_pdf(path)
    meta = extract_document_metadata(path.name, parsed.full_text, parsed.cover_title)

    existing = session.query(Document).filter_by(filename=path.name).one_or_none()
    if existing is not None:
        session.delete(existing)
        session.flush()

    document = Document(
        filename=path.name,
        title=meta.title,
        document_type=meta.document_type,
        policy_id=meta.policy_id,
        product=meta.product,
        authority=meta.authority,
        contractual=meta.contractual,
        effective_date=meta.effective_date,
        issued_date=meta.issued_date,
        version=meta.version,
        page_count=parsed.page_count,
        source_hash=source_hash,
    )
    session.add(document)
    session.flush()

    stem = path.stem
    markdown_path = write_markdown(parsed, meta.title, markdown_dir, stem)

    chunks = build_chunks(parsed, filename=path.name, document_title=meta.title)
    collection = get_collection()
    # Re-ingesting the same file replaces its chunks rather than duplicating them.
    collection.delete(where={"filename": path.name})
    if chunks:
        embeddings = cast(PyEmbeddings, embed_texts([c.text for c in chunks]))
        collection.add(
            ids=[f"{document.id}:{i}" for i in range(len(chunks))],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "filename": c.filename,
                    "document_title": c.document_title,
                    "section_title": c.section_title or "",
                    "section_number": c.section_number or "",
                    "page": c.page,
                    "chunk_type": c.chunk_type,
                }
                for c in chunks
            ],
        )

    session.commit()
    return IngestResult(
        filename=path.name,
        document_id=str(document.id),
        chunks=len(chunks),
        markdown_path=str(markdown_path),
    )

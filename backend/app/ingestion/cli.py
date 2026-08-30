"""CLI: python -m app.ingestion ingest <documents_dir>

Parses every PDF, writes a Markdown copy, embeds its chunks into Chroma, and upserts
Document metadata into Postgres.
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import make_engine
from app.ingestion.loader import ingest_document
from app.rag.vectorstore import reset_collection


def ingest_directory(documents_dir: Path) -> int:
    if not documents_dir.is_dir():
        print(f"error: {documents_dir} is not a directory", file=sys.stderr)
        return 1

    pdf_paths = sorted(documents_dir.glob("*.pdf"))
    if not pdf_paths:
        print(f"error: no PDF files found in {documents_dir}", file=sys.stderr)
        return 1

    settings = get_settings()
    markdown_dir = settings.markdown_dir_path

    reset_collection()

    engine = make_engine()
    with Session(engine) as session:
        for path in pdf_paths:
            result = ingest_document(session, path, markdown_dir)
            print(f"{result.filename:55s} chunks={result.chunks:3d}  -> {result.markdown_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ingestion")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Parse PDFs, write Markdown, embed into Chroma")
    ingest_parser.add_argument("documents_dir", type=Path, help="Directory containing source PDFs")

    args = parser.parse_args(argv)
    if args.command == "ingest":
        return ingest_directory(args.documents_dir)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

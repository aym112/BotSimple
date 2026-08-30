"""Verifies the real ingested corpus: Postgres document metadata, Markdown files on
disk, and the Chroma vector store all agree with the supplied corpus inventory.

Assumes the 12 supplied PDFs have already been ingested via `python -m app.ingestion
ingest` against `policylens_test` / its markdown+chroma dirs.
"""

from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import Document
from app.rag.vectorstore import get_collection


def test_all_twelve_documents_present(db_session):
    count = db_session.scalar(select(func.count()).select_from(Document))
    assert count == 12


def test_policy_scoping_matches_spec_inventory(db_session):
    expected = {
        "POL-2026-0042": 3,
        "POL-2026-0188": 2,
        "POL-2026-0291": 3,
        "LIFE-2026-0137": 3,
    }
    for policy_id, doc_count in expected.items():
        count = db_session.scalar(
            select(func.count()).select_from(Document).where(Document.policy_id == policy_id)
        )
        assert count == doc_count, f"{policy_id} expected {doc_count} documents, got {count}"


def test_glossary_is_non_contractual_and_unscoped(db_session):
    glossary = db_session.execute(
        select(Document).where(Document.document_type == "product_glossary")
    ).scalar_one()
    assert glossary.policy_id is None
    assert glossary.contractual is False
    assert glossary.authority == "informational"


def test_markdown_file_written_per_document(db_session):
    markdown_dir = get_settings().markdown_dir_path
    for document in db_session.execute(select(Document)).scalars().all():
        stem = document.filename.rsplit(".", 1)[0]
        assert (markdown_dir / f"{stem}.md").is_file()


def test_isin_row_is_a_single_chunk():
    # The Fund Annex deliberately also mentions this ISIN in a distractor prose
    # paragraph (SPEC.md's "must not substitute a similar fund name" example) - scope
    # to table-row chunks, which is what an exact-identifier lookup actually wants.
    collection = get_collection()
    result = collection.get(
        where={"chunk_type": "table_row"}, where_document={"$contains": "LU1234567896"}
    )
    assert len(result["ids"]) == 1
    assert "1.20%" in result["documents"][0]


def test_fund_annex_has_24_table_row_chunks():
    collection = get_collection()
    result = collection.get(
        where={
            "$and": [
                {"filename": "11_LIFE-2026-0137_Fund_Annex.pdf"},
                {"chunk_type": "table_row"},
            ]
        }
    )
    assert len(result["ids"]) == 24


def test_reingesting_a_file_does_not_duplicate_chunks(db_session):
    from app.ingestion.loader import ingest_document

    settings = get_settings()
    path = settings.documents_dir_path / "01_POL-2026-0042_Health_Particular_Conditions.pdf"

    before = ingest_document(db_session, path, settings.markdown_dir_path)
    after = ingest_document(db_session, path, settings.markdown_dir_path)

    assert before.chunks == after.chunks
    collection = get_collection()
    result = collection.get(where={"filename": "01_POL-2026-0042_Health_Particular_Conditions.pdf"})
    assert len(result["ids"]) == after.chunks

"""Document-level metadata extraction from filename conventions and in-body text.

Never from data/eval/corpus_manifest.json (SPEC.md section 0.1: that file is
evaluation-only and must not influence ingestion or retrieval).
"""

import re
from dataclasses import dataclass
from datetime import date, datetime

# Matches the corpus's policy/contract id families: POL-2026-0042, LIFE-2026-0137, ...
_POLICY_ID_PATTERN = re.compile(r"\b(POL|LIFE)-\d{4}-\d{4}\b", re.IGNORECASE)

_DOC_TYPE_TOKENS: list[tuple[str, str]] = [
    ("particular_conditions", "particular_conditions"),
    ("general_conditions", "general_conditions"),
    ("endorsement", "endorsement"),
    ("fund_annex", "fund_annex"),
    ("glossary", "product_glossary"),
]

_DATE_PATTERN = re.compile(
    r"(?:Endorsement effective date|Effective date)\s*:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})"
)
_ISSUED_PATTERN = re.compile(r"Issued\s*:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})")
_VERSION_PATTERN = re.compile(r"/\s*(END-\d+)\b")


@dataclass
class DocumentMetadata:
    filename: str
    title: str
    document_type: str
    policy_id: str | None
    product: str | None
    authority: str
    contractual: bool
    effective_date: date | None
    issued_date: date | None
    version: str | None


def _parse_date(text: str) -> date | None:
    try:
        return datetime.strptime(text.strip(), "%d %B %Y").date()
    except ValueError:
        return None


def _infer_document_type(filename: str) -> str:
    lowered = filename.lower()
    for token, doc_type in _DOC_TYPE_TOKENS:
        if token in lowered:
            return doc_type
    return "unknown"


def _infer_policy_id_from_filename(filename: str) -> str | None:
    # Underscores are word characters, so "\bPOL-..." doesn't match right after
    # "01_POL-...": break the filename into space-separated tokens before matching.
    match = _POLICY_ID_PATTERN.search(filename.replace("_", " "))
    return match.group(0).upper() if match else None


def extract_document_metadata(filename: str, full_text: str, cover_title: str | None) -> DocumentMetadata:
    document_type = _infer_document_type(filename)
    policy_id = _infer_policy_id_from_filename(filename)
    contractual = document_type != "product_glossary"

    title = cover_title or filename.rsplit(".", 1)[0].replace("_", " ")
    product = title.split(" - ", 1)[0].strip() if " - " in title else None

    date_match = _DATE_PATTERN.search(full_text)
    effective_date = _parse_date(date_match.group(1)) if date_match else None

    issued_match = _ISSUED_PATTERN.search(full_text)
    issued_date = _parse_date(issued_match.group(1)) if issued_match else None

    version_match = _VERSION_PATTERN.search(full_text)
    version = version_match.group(1) if version_match else None

    return DocumentMetadata(
        filename=filename,
        title=title,
        document_type=document_type,
        policy_id=policy_id,
        product=product,
        authority="contractual" if contractual else "informational",
        contractual=contractual,
        effective_date=effective_date,
        issued_date=issued_date,
        version=version,
    )

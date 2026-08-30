"""The agent's tool surface, as LangChain `@tool`-decorated functions - dedicated,
typed, read-only tools rather than a raw filesystem/bash tool, per Anthropic's
agent-design guidance: promote an action to a dedicated tool when the harness needs to
audit or render it. `@tool` derives each tool's JSON schema from its type hints and
docstring, and LangSmith traces every call automatically (no manual instrumentation)."""

import re
from pathlib import Path

from langchain_core.tools import tool

_PAGE_MARKER = re.compile(r"\*\(page (\d+)\)\*")

from app.config import get_settings
from app.rag.embeddings import embed_query
from app.rag.vectorstore import get_collection


def _pdf_filename(markdown_path: Path) -> str:
    """Tools always report the original PDF's filename, never the derived .md one -
    citations must be consistent regardless of which tool produced them, since only
    the PDF's Markdown twin is what the Evidence pane can render."""
    return f"{markdown_path.stem}.pdf"


@tool
def search_documents(query: str, top_k: int = 5) -> str:
    """Semantic search over the insurance document corpus (particular/general
    conditions, endorsements, the fund annex, the product glossary). Use this for
    conceptual or eligibility questions, or when you don't know the exact wording used
    in the source documents.

    Args:
        query: Natural-language search query.
        top_k: Number of results to return (default 5, max 15).
    """
    top_k = max(1, min(top_k, 15))
    embedding = embed_query(query)
    results = get_collection().query(query_embeddings=[embedding], n_results=top_k)

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if not documents:
        return "No matching passages were found."

    blocks = []
    for text, meta in zip(documents, metadatas, strict=True):
        location = f"{meta['filename']} (p. {meta['page']}"
        if meta.get("section_title"):
            location += f", section: {meta['section_title']}"
        location += ")"
        blocks.append(f"[{location}]\n{text}")

    return "\n\n---\n\n".join(blocks)


@tool
def grep_documents(pattern: str, case_sensitive: bool = False) -> str:
    """Exact keyword or regex search across the Markdown corpus files - use this for
    exact identifiers (policy numbers like POL-2026-0042, ISINs, fund names) or
    specific defined terms where you want every literal occurrence, not a semantic
    approximation.

    Args:
        pattern: Regular expression to search for.
        case_sensitive: Defaults to false.
    """
    markdown_dir = get_settings().markdown_dir_path
    try:
        regex = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
    except re.error as exc:
        return f"Invalid regular expression: {exc}"

    matches: list[str] = []
    for path in sorted(markdown_dir.glob("*.md")):
        current_page = 1
        for line in path.read_text(encoding="utf-8").splitlines():
            page_match = _PAGE_MARKER.search(line)
            if page_match:
                current_page = int(page_match.group(1))
                continue  # the marker line itself is never useful match content
            if regex.search(line):
                matches.append(f"{_pdf_filename(path)} (p. {current_page}): {line.strip()}")
                if len(matches) >= 50:
                    break
        if len(matches) >= 50:
            break

    return "\n".join(matches) if matches else "No matches found."


@tool
def list_documents() -> str:
    """List every document in the corpus with its title and filename."""
    markdown_dir = get_settings().markdown_dir_path
    lines = []
    for path in sorted(markdown_dir.glob("*.md")):
        first_line = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        lines.append(f"{_pdf_filename(path)} - {first_line}")
    return "\n".join(lines)


@tool
def read_document(filename: str) -> str:
    """Read the full Markdown text of one document by filename. Use after
    search_documents or grep_documents point you to a specific file and you need more
    surrounding context than the snippet gave you.

    Args:
        filename: Exact filename, e.g. from a prior search result.
    """
    markdown_dir = get_settings().markdown_dir_path
    stem = Path(filename).stem
    candidate = markdown_dir / f"{stem}.md"
    if not candidate.exists():
        return f"No document found matching '{filename}'."
    return candidate.read_text(encoding="utf-8")


TOOLS = [search_documents, grep_documents, list_documents, read_document]

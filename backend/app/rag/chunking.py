"""Splits a parsed PDF into embeddable chunks, built directly from the structured
`ParsedDocument` (not by re-parsing the Markdown text back apart) so chunk metadata
(page, section) stays exact.

Table rows are always their own chunk (one fund/benefit per embedding, header-labeled
via `serialize_table_row`) - collapsing a 24-row table into one blob would dilute a
single-fund question across everything else in the table. Prose is grouped by heading
section, capped so long sections don't turn into oversized embeddings.
"""

from dataclasses import dataclass

from app.ingestion.pdf_parser import HeadingItem, ParagraphItem, ParsedDocument, TableRowItem
from app.ingestion.table_serializer import serialize_table_row
from app.text_utils import strip_bullet

_MAX_CHUNK_CHARS = 2000


@dataclass
class Chunk:
    text: str
    filename: str
    document_title: str
    section_title: str | None
    section_number: str | None
    page: int
    chunk_type: str  # "table_row" | "section"


def build_chunks(parsed: ParsedDocument, filename: str, document_title: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    current_heading: HeadingItem | None = None
    buffer: list[str] = []
    buffer_page: int | None = None

    def flush() -> None:
        nonlocal buffer, buffer_page
        if buffer:
            chunks.append(
                Chunk(
                    text="\n\n".join(buffer),
                    filename=filename,
                    document_title=document_title,
                    section_title=current_heading.text if current_heading else None,
                    section_number=current_heading.section_number if current_heading else None,
                    page=buffer_page or 1,
                    chunk_type="section",
                )
            )
        buffer = []
        buffer_page = None

    for page in parsed.pages:
        for item in page.items:
            if isinstance(item, HeadingItem):
                flush()
                current_heading = item

            elif isinstance(item, ParagraphItem):
                text = f"- {strip_bullet(item.text)}" if item.unit_type == "list_item" else item.text
                current_len = sum(len(b) for b in buffer)
                if buffer and current_len + len(text) > _MAX_CHUNK_CHARS:
                    flush()
                if not buffer:
                    buffer_page = item.page
                buffer.append(text)

            elif isinstance(item, TableRowItem):
                flush()
                chunks.append(
                    Chunk(
                        text=serialize_table_row(item.header, item.values),
                        filename=filename,
                        document_title=document_title,
                        section_title=current_heading.text if current_heading else None,
                        section_number=current_heading.section_number if current_heading else None,
                        page=item.page,
                        chunk_type="table_row",
                    )
                )

    flush()
    return chunks

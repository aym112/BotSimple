"""PyMuPDF-based PDF parsing into a library-independent internal representation.

Docling is deferred to slice 2 (SPEC.md calls for both Docling + PyMuPDF; slice 1 uses
PyMuPDF alone — see docs/decisions.md). Downstream ingestion code depends only on the
dataclasses below, never on `pymupdf`/`fitz` types directly, so adding Docling later
means changing this module only.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import pymupdf

_FOOTER_MARGIN_PT = 50.0
_HEADING_MIN_SIZE = 12.0
_HEADING_MAX_SIZE = 18.0  # >= this is treated as the document's cover title, not a section
_LEADING_NUMBER = re.compile(r"^(\d+(?:\.\d+)*)\.?\s*(.*)$")


@dataclass
class HeadingItem:
    page: int
    text: str
    section_number: str | None
    level: int


@dataclass
class ParagraphItem:
    page: int
    text: str
    unit_type: str  # "paragraph" | "list_item"
    bbox: tuple[float, float, float, float]


@dataclass
class TableRowItem:
    page: int
    table_id: str
    row_index: int
    header: list[str]
    values: list[str]
    bbox: tuple[float, float, float, float] | None


PageItem = HeadingItem | ParagraphItem | TableRowItem


@dataclass
class ParsedPage:
    page_number: int
    items: list[PageItem] = field(default_factory=list)


@dataclass
class ParsedDocument:
    page_count: int
    pages: list[ParsedPage]
    full_text: str
    cover_title: str | None


def _bbox_overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0


def _classify_heading(text: str) -> tuple[str | None, str, int]:
    match = _LEADING_NUMBER.match(text)
    if match and match.group(2):
        section_number = match.group(1)
        title = match.group(2).strip()
        level = section_number.count(".") + 1
        return section_number, title, level
    return None, text, 1


def parse_pdf(path: Path) -> ParsedDocument:
    doc = pymupdf.open(str(path))
    pages: list[ParsedPage] = []
    full_text_parts: list[str] = []
    cover_title: str | None = None

    for page_index in range(doc.page_count):
        page_number = page_index + 1
        page = doc[page_index]
        page_height = page.rect.height
        full_text_parts.append(cast(str, page.get_text()))

        # PyMuPDF's stubs type these loosely (str / possibly-None); the shapes are
        # documented and stable, so a boundary cast keeps the rest of this function
        # meaningfully typed instead of `Any`-infected end to end.
        found_tables = page.find_tables()
        assert found_tables is not None
        table_bboxes = [tuple(t.bbox) for t in found_tables.tables]

        # (y0, item) pairs so text blocks and tables can be merged into one reading-order stream.
        positioned: list[tuple[float, PageItem]] = []

        for table_index, table in enumerate(found_tables.tables):
            header = [(h or "").strip() for h in table.header.names]
            rows = table.extract()
            data_rows = rows[1:] if rows and rows[0] == table.header.names else rows
            table_id = f"p{page_number}-t{table_index}"
            bbox = tuple(table.bbox)
            for row_index, row in enumerate(data_rows):
                values = [(cell or "").strip() for cell in row]
                if not any(values):
                    continue
                item = TableRowItem(
                    page=page_number,
                    table_id=table_id,
                    row_index=row_index,
                    header=header,
                    values=values,
                    bbox=bbox,
                )
                positioned.append((bbox[1], item))

        text_dict = cast(dict[str, Any], page.get_text("dict"))
        for block in text_dict["blocks"]:
            if block.get("type") != 0:
                continue
            bbox: tuple[float, float, float, float] = tuple(block["bbox"])
            if any(_bbox_overlaps(bbox, tb) for tb in table_bboxes):
                continue
            if bbox[1] > page_height - _FOOTER_MARGIN_PT:
                continue  # footer band (page label / doc name repeated on every page)

            lines = block["lines"]
            if not lines or not lines[0]["spans"]:
                continue
            first_span = lines[0]["spans"][0]
            size = first_span["size"]
            is_bold = "Bold" in first_span.get("font", "")
            text = "\n".join(
                "".join(span["text"] for span in line["spans"]) for line in lines
            ).strip()
            if not text:
                continue

            if size >= _HEADING_MAX_SIZE:
                if cover_title is None:
                    cover_title = text
                continue

            if is_bold and size >= _HEADING_MIN_SIZE:
                section_number, title, level = _classify_heading(text)
                positioned.append(
                    (bbox[1], HeadingItem(page=page_number, text=title, section_number=section_number, level=level))
                )
            else:
                unit_type = "list_item" if not text[0].isalnum() else "paragraph"
                positioned.append(
                    (bbox[1], ParagraphItem(page=page_number, text=text, unit_type=unit_type, bbox=bbox))
                )

        positioned.sort(key=lambda pair: pair[0])
        pages.append(ParsedPage(page_number=page_number, items=[item for _, item in positioned]))

    return ParsedDocument(
        page_count=doc.page_count,
        pages=pages,
        full_text="\n".join(full_text_parts),
        cover_title=cover_title,
    )

"""Renders a parsed PDF to a Markdown file on disk.

The Markdown copy is the corpus the agent's grep tool searches directly - plain text,
one file per document, tables kept as Markdown tables. Keeping this as real files (not
just DB rows) is what makes a filesystem-style grep tool possible at all.
"""

from pathlib import Path

from app.ingestion.pdf_parser import HeadingItem, ParagraphItem, ParsedDocument, TableRowItem
from app.text_utils import strip_bullet


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(parsed: ParsedDocument, title: str) -> str:
    lines: list[str] = [f"# {title}", ""]
    current_page: int | None = None
    current_table_id: str | None = None

    for page in parsed.pages:
        for item in page.items:
            if item.page != current_page:
                current_page = item.page
                current_table_id = None
                lines.append(f"*(page {current_page})*")
                lines.append("")

            if isinstance(item, HeadingItem):
                current_table_id = None
                level = min(item.level + 1, 6)
                heading_text = f"{item.section_number} {item.text}" if item.section_number else item.text
                lines.append(f"{'#' * level} {heading_text}")
                lines.append("")

            elif isinstance(item, ParagraphItem):
                current_table_id = None
                if item.unit_type == "list_item":
                    lines.append(f"- {strip_bullet(item.text)}")
                else:
                    lines.append(item.text)
                lines.append("")

            elif isinstance(item, TableRowItem):
                if item.table_id != current_table_id:
                    current_table_id = item.table_id
                    header_cells = [_escape_cell(h) or f"Column {i + 1}" for i, h in enumerate(item.header)]
                    lines.append("| " + " | ".join(header_cells) + " |")
                    lines.append("| " + " | ".join("---" for _ in header_cells) + " |")
                row_cells = [_escape_cell(v) for v in item.values]
                lines.append("| " + " | ".join(row_cells) + " |")

    return "\n".join(lines).strip() + "\n"


def write_markdown(parsed: ParsedDocument, title: str, output_dir: Path, stem: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{stem}.md"
    path.write_text(render_markdown(parsed, title), encoding="utf-8")
    return path

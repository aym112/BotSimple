"""Header-labeled table row serialization — SPEC.md section 17.

A table row keeps its header semantics as searchable text (`Benefit: Dental care\\n
Annual limit: EUR 1,200\\n...`) instead of collapsing to a bare pipe-delimited row,
so lexical retrieval and the generator both see what each value means.
"""


def serialize_table_row(header: list[str], values: list[str]) -> str:
    lines = []
    for index, value in enumerate(values):
        column_name = header[index].strip() if index < len(header) and header[index] else f"Column {index + 1}"
        lines.append(f"{column_name}: {value.strip()}")
    return "\n".join(lines)

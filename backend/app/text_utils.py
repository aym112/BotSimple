def strip_bullet(text: str) -> str:
    """The source PDFs' bullet glyph often decodes as a replacement character - drop
    whatever non-alphanumeric marker starts the line rather than keeping "� Foo"."""
    stripped = text.lstrip()
    if stripped and not stripped[0].isalnum():
        stripped = stripped[1:].lstrip()
    return stripped

from app.ingestion.table_serializer import serialize_table_row


def test_serializes_header_labeled_rows():
    header = ["Benefit", "Annual limit", "Deductible", "Network"]
    values = ["Dental care", "EUR 1,200", "EUR 100", "Partner preferred"]
    text = serialize_table_row(header, values)
    assert text == (
        "Benefit: Dental care\n"
        "Annual limit: EUR 1,200\n"
        "Deductible: EUR 100\n"
        "Network: Partner preferred"
    )


def test_missing_header_gets_placeholder_column_name():
    text = serialize_table_row(["Fund"], ["Nova Global Equity", "LU1234567896"])
    assert text == "Fund: Nova Global Equity\nColumn 2: LU1234567896"


def test_strips_whitespace_around_values():
    text = serialize_table_row(["Benefit "], ["  Dental care  "])
    assert text == "Benefit: Dental care"

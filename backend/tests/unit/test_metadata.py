from datetime import date

from app.ingestion.metadata import extract_document_metadata


class TestFilenamePolicyIdExtraction:
    def test_policy_id_after_leading_number_and_underscore(self):
        # Regression: "01_POL-2026-0042_..." — \b doesn't fire right after "_" (a word
        # char), so a naive regex on the raw filename misses the id entirely.
        meta = extract_document_metadata(
            "01_POL-2026-0042_Health_Particular_Conditions.pdf", full_text="", cover_title=None
        )
        assert meta.policy_id == "POL-2026-0042"

    def test_life_prefixed_id(self):
        meta = extract_document_metadata(
            "09_LIFE-2026-0137_LifeInvest_Particular_Conditions.pdf", full_text="", cover_title=None
        )
        assert meta.policy_id == "LIFE-2026-0137"

    def test_glossary_has_no_policy_id(self):
        meta = extract_document_metadata(
            "12_Nova_Product_Glossary_and_FAQ.pdf", full_text="", cover_title=None
        )
        assert meta.policy_id is None
        assert meta.contractual is False
        assert meta.authority == "informational"


class TestDocumentTypeInference:
    def test_particular_conditions(self):
        meta = extract_document_metadata("06_POL-2026-0291_Home_Particular_Conditions.pdf", "", None)
        assert meta.document_type == "particular_conditions"
        assert meta.contractual is True

    def test_endorsement(self):
        meta = extract_document_metadata("03_POL-2026-0042_Health_Endorsement_01.pdf", "", None)
        assert meta.document_type == "endorsement"

    def test_fund_annex(self):
        meta = extract_document_metadata("11_LIFE-2026-0137_Fund_Annex.pdf", "", None)
        assert meta.document_type == "fund_annex"


class TestEffectiveDateExtraction:
    def test_plain_effective_date_label(self):
        meta = extract_document_metadata(
            "01_POL-2026-0042_Health_Particular_Conditions.pdf",
            full_text="Policy number: POL-2026-0042\nEffective date: 01 January 2026\n",
            cover_title=None,
        )
        assert meta.effective_date == date(2026, 1, 1)

    def test_endorsement_effective_date_label(self):
        meta = extract_document_metadata(
            "03_POL-2026-0042_Health_Endorsement_01.pdf",
            full_text="Endorsement effective date: 01 June 2026\nIssued: 20 May 2026\n",
            cover_title=None,
        )
        assert meta.effective_date == date(2026, 6, 1)
        assert meta.issued_date == date(2026, 5, 20)

    def test_no_date_present_returns_none(self):
        meta = extract_document_metadata("02_POL-2026-0042_Health_General_Conditions.pdf", "", None)
        assert meta.effective_date is None


class TestTitleAndProduct:
    def test_uses_cover_title_and_splits_product(self):
        meta = extract_document_metadata(
            "01_POL-2026-0042_Health_Particular_Conditions.pdf",
            full_text="",
            cover_title="Nova Health Premium - Particular Conditions",
        )
        assert meta.title == "Nova Health Premium - Particular Conditions"
        assert meta.product == "Nova Health Premium"

    def test_falls_back_to_humanized_filename_without_cover_title(self):
        meta = extract_document_metadata("06_POL-2026-0291_Home_Particular_Conditions.pdf", "", None)
        assert "Home" in meta.title

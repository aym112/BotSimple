"""SPEC.md section 8's acceptance questions, run against the real agent (real OpenAI
calls - skipped automatically when OPENAI_API_KEY isn't configured). Assertions are
loose substring/citation checks, not exact-string matches: an LLM's phrasing varies
even when the underlying fact is correct and deterministic."""

import pytest

from app.config import get_settings
from app.rag.agent import run_agent_query

pytestmark = pytest.mark.skipif(
    not get_settings().openai_api_key, reason="OPENAI_API_KEY not configured"
)

CASES = [
    ("Q01", "For policy POL-2026-0042, what is the current annual dental care limit?", "1,500", "Endorsement"),
    ("Q03", "For POL-2026-0042, what is the dental deductible?", "100", "Particular_Conditions"),
    ("Q06", "What is the personal belongings limit for POL-2026-0188?", "1,000", "Motor"),
    ("Q07", "For POL-2026-0291, what is the current water damage deductible?", "500", "Home"),
    ("Q09", "What is the management fee for ISIN LU1234567896?", "1.20", "Fund_Annex"),
    ("Q10", "What is the management fee for ISIN LU1616161615?", "1.55", "Fund_Annex"),
    ("Q11", "How many free online fund switches per calendar year are included in LIFE-2026-0137?", "6", "LifeInvest"),
    ("Q12", "What is the management fee of Nova Global Infrastructure?", "1.15", "Fund_Annex"),
]


@pytest.mark.parametrize("qid,question,expected_value,expected_source", CASES, ids=[c[0] for c in CASES])
def test_acceptance_question(qid, question, expected_value, expected_source):
    result = run_agent_query(question)
    assert expected_value in result.answer, f"{qid}: expected '{expected_value}' in {result.answer!r}"
    assert result.citations, f"{qid}: expected at least one citation"
    assert any(expected_source in c.filename for c in result.citations), (
        f"{qid}: expected a citation containing '{expected_source}', got {[c.filename for c in result.citations]}"
    )


def test_q04_abstains_when_topic_is_absent():
    result = run_agent_query("Does POL-2026-0042 cover osteopathy?")
    lowered = result.answer.lower()
    assert any(phrase in lowered for phrase in ["cannot confirm", "no mention", "not find", "does not state", "no provision"])


def test_q05_cross_reference_excludes_visible_belongings():
    result = run_agent_query(
        "For POL-2026-0188, is a laptop stolen from the passenger seat of a locked unattended car covered?"
    )
    assert "not covered" in result.answer.lower() or result.answer.lower().startswith("no")


def test_q08_negligence_does_not_automatically_exclude():
    result = run_agent_query(
        "Does ordinary negligence automatically exclude water damage under POL-2026-0291?"
    )
    assert "no" in result.answer.lower().split(".")[0].lower()


def test_uses_grep_for_exact_isin_lookup():
    result = run_agent_query("What is the management fee for ISIN LU1234567896?")
    tool_names = {t.tool for t in result.tool_calls}
    assert "grep_documents" in tool_names or "search_documents" in tool_names

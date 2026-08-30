"""Manual smoke test of the agent against the real ingested corpus."""

from app.rag.agent import run_agent_query

QUESTIONS = [
    "For policy POL-2026-0042, what is the current annual dental care limit?",
    "What is the management fee for ISIN LU1234567896?",
    "Does POL-2026-0042 cover osteopathy?",
]


def main():
    for question in QUESTIONS:
        result = run_agent_query(question)
        print(f"--- {question} ---")
        print("answer:", result.answer)
        print("citations:", [(c.filename, c.page) for c in result.citations])
        print("tool_calls:", [(t.tool, t.input) for t in result.tool_calls])
        print()


if __name__ == "__main__":
    main()

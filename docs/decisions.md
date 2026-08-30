# AymanChat — implementation decisions

This project pivoted away from an earlier deterministic-first architecture spec to a real
LLM agent with tools. This document reflects the current, actual system.

## Why an agent instead of a deterministic pipeline

The original design (anchors → scope filters → lexical ranking → precedence rules → a
fake/regex answer generator) worked, but every new question pattern needed a new
heuristic, and the result was a lot of code to approximate what an LLM already does well:
read evidence, decide what's relevant, and explain a nuanced answer in plain language.
The trade-off is real — an agent's phrasing isn't byte-for-byte reproducible the way a
regex extractor's was, and it costs real API calls — but for a document-QA chatbot the
flexibility is worth it. Correctness is checked with substring/citation assertions
(`backend/tests/integration/test_agent.py`), not exact-string matches.

## Why Markdown files on disk, not just database rows

Each PDF is parsed once and rendered to a real `.md` file (`app/ingestion/markdown_writer.py`)
in addition to being chunked for embeddings. This is what makes a genuine grep tool
possible: `grep_documents` (`app/rag/tools.py`) runs a regex directly over these files,
the same way a coding agent greps a codebase. It's also just more inspectable — you can
open any document's Markdown and see exactly what the agent can see.

## Why LangGraph's prebuilt agent, not a hand-rolled tool loop

The agent was first built as a manual `while` loop directly against the OpenAI SDK
(build messages, call `chat.completions.create`, execute `tool_calls`, repeat). It
worked, but every mechanic - message-shape bookkeeping, structured-output finalize pass,
tool-call trace reconstruction - was code we owned for no real benefit over LangGraph's
`create_agent` (from `langchain.agents`), which is the same ReAct loop pre-built: give it
a model, a list of `@tool`-decorated functions, and a `response_format` Pydantic model,
and it runs the loop and the structured finalize pass itself. `RECURSION_LIMIT` (15) is
the loop's bound, playing the same role the old `MAX_ITERATIONS` did.

This also fixed the observability story. Tracing every OpenAI call by hand
(`langsmith.wrappers.wrap_openai`) worked but needed careful attention to *when* the
LangSmith env vars got set - `@traceable` decorators (and, we learned the hard way,
LangChain's own auto-tracing) check `LANGSMITH_TRACING` at *import* time, not call time,
so setting it lazily inside a request handler silently no-oped tracing for the rest of
the process. `app/config.py` now sets it at module import time, before anything that
could get decorated. With LangChain/LangGraph, tracing is otherwise completely automatic
- no `wrap_openai`, no manual `@traceable` calls - and LangSmith gives each tool its own
named span (`search_documents`, `grep_documents`, ...) rather than one generic
`execute_tool` span, which is strictly better observability than the hand-rolled version
produced.

## Why Chroma, not pgvector

Dense retrieval needs a vector store; Postgres/pgvector would have meant running and
deploying a database extension for a corpus of 12 documents. Chroma is embedded
(`PersistentClient`, no server) and persists to a plain directory
(`CHROMA_DIR`), which keeps local dev and deployment identical — no separate service to
provision. Postgres is still used, just for what it's actually good at here: the
`documents` metadata table (corpus browser, PDF serving) and `query_requests` (trace
logging).

## Why table rows are always their own chunk

`app/rag/chunking.py` never lets a table (e.g. the Fund Annex's 24 funds) collapse into
one giant embedding — each row is serialized as header-labeled lines (`Benefit: Dental
care\nAnnual limit: EUR 1,200\n...`, `app/ingestion/table_serializer.py`) and embedded on
its own. A single-fund question shouldn't have to compete semantically against 23 other
funds' worth of text in the same chunk.

## Why two retrieval tools instead of one

`search_documents` (semantic, via OpenAI embeddings + Chroma) and `grep_documents`
(exact regex over the Markdown files) are separate, dedicated tools rather than one
fuzzy "search" tool or a raw filesystem/bash tool — dedicated tools are typed,
individually auditable in the trace, and let the agent pick the right retrieval mode
itself (exact identifiers → grep, conceptual questions → semantic search) rather than
guessing at query-rewriting to make one tool do both jobs.

## Why the final answer is a structured-output pass

The tool-use turns are free-form (the model decides what to call and when to stop).
`response_format=StructuredAnswer` on `create_agent` (`app/rag/agent.py`) makes LangGraph
run one more request internally once the tool loop ends, restating the answer as
`{answer, citations}`. This guarantees the API always returns a clean, parseable shape
regardless of how many tool calls happened in between, without constraining the tool-use
reasoning itself - and it's LangGraph's job now, not a second call we manage ourselves.

## Why the frontend shows real signals only

`StatusBadges` shows exactly one thing: whether the answer carries a citation. Earlier
badges ("Evidence verified", "Complete answer") were leftover language from the
deterministic design and had stopped meaning anything once the pipeline changed — a
badge that always shows true or is decorative is worse than no badge. `TraceDrawer` shows
the actual tool calls the agent made (`tool`, `input`, `output_summary`) instead of a
synthetic pipeline-stage timeline.

## What's out of scope (unchanged from the original plan)

Signup, multi-user/RBAC, document upload, OCR, a knowledge graph, billing, an admin
panel. The corpus is fixed and small (12 PDFs) so the effort goes into retrieval quality
and citation correctness, not document-management infrastructure a real production
system would need but this prototype doesn't need to prove.

## Known limitations

- **Non-determinism.** The same question can be answered with different wording (and
  occasionally a different tool-call sequence) across runs. Tests assert on substrings
  and citation filenames, not exact strings.
- **Cost.** Every query makes at least two OpenAI calls (the tool-use loop, then the
  structured-output finalize pass), plus one embedding call per `search_documents`
  invocation.
- **Shared Chroma store across dev/test.** Unlike Postgres (`DATABASE_URL` vs
  `DATABASE_URL_TEST`), there is one `CHROMA_DIR` — integration tests read whatever
  corpus is currently ingested there rather than an isolated fixture. Fine for a
  single-developer project with a fixed 12-document corpus; would need a real fixture
  store for CI running in parallel with dev.

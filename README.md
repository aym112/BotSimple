# AymanChat

**A real LLM agent that answers questions from an insurance document corpus, with citations.**

AymanChat is a chatbot backed by an OpenAI agent with tools — it decides for itself how
to answer a question (grep for an exact identifier, semantically search the corpus, read
a full document) rather than following a fixed retrieval pipeline. Why: see
[`docs/decisions.md`](docs/decisions.md).

Note: this project originally followed a different, fully deterministic architecture
described in [`SPEC.md`](SPEC.md); it has since moved to the agentic design described
here, which `docs/decisions.md` explains. `SPEC.md` is kept for history but no longer
reflects the current system.

## What's built

- **Ingestion** (`backend/app/ingestion/`): parses the 12 supplied PDFs (PyMuPDF),
  writes a Markdown copy of each to disk, extracts basic metadata (policy id, document
  type, effective dates), and chunks + embeds the content into a local Chroma vector
  store (table rows are always their own chunk — see `docs/decisions.md`).
- **Agent** (`backend/app/rag/agent.py`): a LangGraph `create_agent` ReAct agent
  (`gpt-5.4-mini` by default, via `langchain-openai`) with four LangChain `@tool`
  functions — `search_documents` (semantic), `grep_documents` (exact regex over the
  Markdown files), `list_documents`, `read_document` — that loops until it has enough
  evidence, then produces a structured `{answer, citations}` response. LangSmith traces
  every model and tool call automatically when `LANGSMITH_TRACING=true`.
- **API**: demo login (JWT in an HttpOnly cookie), `POST /api/v1/query`,
  `GET /api/v1/requests/{id}` and `/trace`, a documents/corpus browser, PDF serving.
- **Frontend**: login, chat with citations, an Evidence pane that opens the cited PDF at
  the right page, a "How this answer was built" drawer showing the agent's actual tool
  calls, and a documents browser.

## Running it locally

```bash
cp .env.example .env
# edit .env: set AUTH_SECRET to a random string, set OPENAI_API_KEY,
# generate DEMO_PASSWORD_HASH below

docker compose up -d db

cd backend
uv sync
uv run python -m alembic upgrade head
uv run python -m app.auth.hash_password "your-password"   # paste into .env's DEMO_PASSWORD_HASH
uv run python -m app.ingestion ingest ../data/documents
uv run python -m uvicorn app.main:app --reload --port 8001

# in a second terminal
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, log in with `DEMO_USERNAME` / the password you hashed above.

Note: `docker-compose.yml` maps Postgres to host port **5433**, not 5432 — this avoids
colliding with a native Postgres service some machines already have running on 5432.
Adjust `DATABASE_URL`/`DATABASE_URL_TEST` in `.env` if you change it.

### Tests

```bash
cd backend
uv run python -m pytest tests/unit -q          # no external services needed
uv run python -m pytest tests/integration -q   # needs `db` running + the corpus ingested
                                                 # into policylens_test; OpenAI-dependent
                                                 # tests auto-skip without OPENAI_API_KEY
```

(`uv run pytest` may be blocked by this environment's Application Control policy on some
Windows machines — use `uv run python -m pytest` instead.)

```bash
cd frontend
npm run build      # tsc -b && vite build
```

## Repository layout

```
backend/    FastAPI app, ingestion CLI, agent + tools, tests
frontend/   React + TypeScript + Vite UI
data/       supplied corpus (documents/), derived markdown/ and chroma/ (git-ignored)
docs/       decisions.md — why the system is built this way
```

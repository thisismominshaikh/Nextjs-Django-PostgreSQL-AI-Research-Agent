

## Architecture Overview

The system is a single Django application with one REST endpoint that does everything: clones the repo (shallow, `--depth 1`), starts a research session row in the database, runs an LLM agent loop that reads the codebase using filesystem tools and writes intermediate conclusions to the DB, then returns the completed session as JSON. No CLI, no frontend — pure REST API consumed via Postman or curl.

The agent lives in `research/agent/grok_runner.py`. It runs as a bounded `for` loop (max `AGENT_MAX_TOOL_ROUNDS`, default 24) that sends conversation history to Groq, executes whatever tool calls the model requests, and exits when the model returns plain text (the final answer).

---

## LLM Choice: Groq / llama-3.3-70b-versatile

Groq was chosen over GPT-4 and Claude for three reasons:

1. **OpenAI-compatible `tool_calls` API** — the `tools` + `tool_choice="auto"` pattern maps directly to our `_TOOL_DECLARATIONS` list without an adapter layer (see `grok_runner.py` lines 15–127).
2. **LPU latency** — Groq's inference hardware keeps per-round latency under a second; important when an agent run may take 10–20 round-trips.
3. **Free-tier access** — a `GROQ_API_KEY` requires no billing setup, lowering friction for the reviewer.

**Trade-off accepted:** Groq enforces tighter rate limits than OpenAI. Heavy burst use hits 429s. Mitigation: the `AGENT_MAX_TOOL_ROUNDS` cap bounds burst size per session.

---

## Database Schema Rationale

Four tables, each with a specific reason to exist:

**`Repository`** — normalized identity record keyed on `identifier` (the repo URL). `unique=True` on `identifier` (line 14, `models.py`) lets `get_or_create` work safely — the same URL submitted from two concurrent sessions cannot create duplicate rows.

**`ResearchSession`** — one question → one answer. The interesting field is `references_json` (line 54, `models.py`): stored as a `JSONField`, not a child table. References are always read alongside the session and never filtered by individual field — a child table would add a JOIN on every read with zero query benefit.

**`Finding`** — agent-authored notes written mid-run via the `save_finding` tool. These are first-class rows (not embedded in the session JSON) so the agent can write them incrementally, and — critically — they survive across sessions for the same repo. The second time someone asks about the same codebase, prior findings are pre-loaded into the initial prompt, saving 1–3 tool round-trips.

**`ToolCallLog`** — audit trail. Each entry is written *before* the result is fed back to the model (`grok_runner.py`, see the `db_tools.log_tool_call` call inside the tool loop). This ordering is deliberate: if the runner crashes mid-run, the log still records every tool executed up to that point.

**What I'd change at scale:** `references_json` would stay as JSON (the access pattern doesn't change). `ToolCallLog` rows could be partitioned by `created_at` at high volume. The current schema has no indexes on `Finding.session__repository` beyond the FK — adding one would matter at thousands of repos.

---

## Agent–DB Interaction

The DB is not just a log dump. It participates in the agent's reasoning:

- **Session start:** prior findings + past session summaries are pre-loaded into the first user message (lines 241–252, `grok_runner.py`), reducing redundant re-exploration.
- **Mid-run:** the agent calls `save_finding` to persist intermediate conclusions tied to file paths.
- **On repeat visits:** those findings surface in context on the next session for the same repo.

---

## Context Management & Cost Controls

Three hard limits (all env-overridable, `settings.py` lines 163–165):

| Setting | Default | Controls |
|---|---|---|
| `AGENT_MAX_TOOL_ROUNDS` | 24 | Groq API spend per session |
| `AGENT_READ_FILE_MAX_CHARS` | 120 000 | Prompt size (context window safety) |
| `AGENT_SEARCH_MAX_MATCHES` | 40 | Latency on large repos |

`get_file_summary` gives the model a cheap outline (size, line count, top-level `def`/`class` list) before it commits to a full `read_file`, reducing wasted token reads.

---

## What I'd Do Differently With More Time

1. **Async execution** — the synchronous POST blocks for the full agent run (20–60 s on a cold clone). Production pattern: return `{session_id, status: "pending"}` immediately, run the agent in a Celery worker, client polls `GET /api/sessions/<id>/`.
2. **Streaming** — Groq supports streaming completions. Surfacing intermediate reasoning to the client in real time would improve perceived responsiveness.
3. **Semantic search via pgvector** — `search_code` is substring-only (Ctrl+F across the repo). Embedding file summaries into a pgvector column would enable semantic retrieval ("find files related to auth" even if the word "auth" isn't literal).
4. **Rate limiting** — no per-IP or per-repo throttle today. DRF's `AnonRateThrottle` would be a 5-line addition.

---

## AI Tool Usage

Claude (claude.ai) was used throughout:

- **Drafted** the initial agent loop in `grok_runner.py` — adapting the OpenAI SDK pattern to Groq's SDK; I corrected the tool-result message format and rewrote the stopping logic.
- **Generated** `seed_sample_data` management command boilerplate (lightly edited).
- **Wrote** the `_split_answer_and_references` parser from a description I provided; I kept it after testing.

Everything else — the 4-table schema, tool set design, security layers in `filesystem_tools.py`, the tool-log ordering decision, the `StartResearchSessionSerializer` as a plain validator — was designed by hand first, then implemented with AI help where it saved time.

---

## Known Limitations

- Synchronous execution blocks the server process for the full agent run.
- No authentication or multi-user isolation.
- `search_code` is substring-only; no semantic retrieval.
- No rate limiting on the start-session endpoint.

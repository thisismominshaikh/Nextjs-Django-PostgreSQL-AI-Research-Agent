# CodeFusion Research Agent

A Django-based AI agent that answers technical questions about GitHub repositories
by exploring the code itself using **Groq** with tool-calling.

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd codefusion_research

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your-key-here

# 5. Run migrations
python manage.py migrate

# 6. Seed sample records (no API key needed)
python manage.py seed_sample_data

# 7. Create Django admin superuser (optional)
python manage.py createsuperuser

# 8. Start the server
python manage.py runserver
```

The API is now available at `http://localhost:8000/`.

---

## API Endpoints

All endpoints accept and return JSON. No authentication required.

### `GET /`
Discovery document listing all routes.

### `POST /api/sessions/start/`
Start a new research session. The agent clones the repo (if needed), runs
the Groq tool-calling loop, and returns when complete.

**Body:**
```json
{
  "repo_url": "https://github.com/tiangolo/fastapi",
  "question": "How does dependency injection work?"
}
```

**Response:** Full session object with `final_answer`, `references_json`, and `status`.

### `GET /api/sessions/<id>/`
Retrieve a session with its findings and full tool-call audit log.

### `GET /api/sessions/<id>/findings/`
List all agent-authored findings for a specific session.

### `GET /api/repositories/`
List all repositories that have been analyzed. Supports `?search=<str>`.

### `GET /api/repositories/sessions/?repo_url=<url>`
List all past sessions for a specific repository.

---

## Using with Postman

1. Import the API — base URL is `http://localhost:8000`
2. All `POST` requests: set `Content-Type: application/json` header
3. No CSRF token required (all endpoints are `csrf_exempt`)

**Example POST body for `/api/sessions/start/`:**
```json
{
  "repo_url": "https://github.com/celery/celery",
  "question": "Where is task retry logic implemented?"
}
```

---

## Seed Data

Run `python manage.py seed_sample_data` to populate the database with realistic
records from two real repositories (FastAPI and Celery) without needing an API key.

Use `--clear` to wipe and re-seed: `python manage.py seed_sample_data --clear`

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | — | Your Groq API key |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model to use |
| `DJANGO_SECRET_KEY` | No | dev default | Django secret key |
| `DJANGO_DEBUG` | No | `true` | Enable debug mode |
| `AGENT_MAX_TOOL_ROUNDS` | No | `24` | Max tool calls per session |
| `AGENT_READ_FILE_MAX_CHARS` | No | `120000` | Max chars read from a file |
| `AGENT_SEARCH_MAX_MATCHES` | No | `40` | Max search results returned |
| `REPO_WORKDIR` | No | `./repo_workdir` | Where repos are cloned |

---

## Database Schema

| Table | Purpose |
|---|---|
| `Repository` | Unique repo URL/path; tracks last analyzed timestamp |
| `ResearchSession` | One question + answer pair; tracks status, tokens, references |
| `Finding` | Agent-authored notes tied to files; persists across sessions |
| `ToolCallLog` | Full audit trail of every tool call with arguments and results |

---

## Admin

Visit `http://localhost:8000/admin/` — sessions show inline findings and tool calls.

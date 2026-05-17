from __future__ import annotations

# [MOMIN] LLM choice: Groq with llama-3.3-70b-versatile.
# [MOMIN] Chosen for three concrete reasons:
# [MOMIN]   1. Native OpenAI-compatible tool_calls API — maps directly to our
# [MOMIN]      _TOOL_DECLARATIONS dict without an adapter layer.
# [MOMIN]   2. Groq LPU hardware delivers sub-second first-token latency;
# [MOMIN]      important for an agent loop that may run 10-24 round-trips.
# [MOMIN]   3. llama-3.3-70b-versatile is free-tier accessible with GROQ_API_KEY.
# [MOMIN] Trade-off accepted: stricter rate limits than OpenAI; back-pressure
# [MOMIN] appears as 429 errors on long runs, not correctness bugs.

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from groq import Groq
from django.conf import settings
from django.utils import timezone

from research.models import Repository, ResearchSession
from research.services import db_tools, filesystem_tools

_TOOL_DECLARATIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories under a path relative to the repository root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to repo root. Use '.' for root.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file with optional 1-based inclusive line range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root."},
                    "start_line": {"type": "integer", "description": "First line to read (1-based)."},
                    "end_line": {"type": "integer", "description": "Last line to read (1-based, inclusive)."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for a substring across text-like source files in the repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Substring to search for."},
                    "glob_pattern": {
                        "type": "string",
                        "description": "Optional glob relative to root (e.g. '**/*.py'). Defaults to **/*.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_summary",
            "description": "Summarize a file: size, line count, preview, and top-level structure hints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_finding",
            "description": "Persist an intermediate conclusion to the database for this session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "integer", "description": "ID of the current research session."},
                    "file_path": {"type": "string", "description": "Relative path of the relevant file."},
                    "note": {"type": "string", "description": "The conclusion or insight to persist."},
                },
                "required": ["session_id", "note"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_previous_findings",
            "description": "Read prior saved findings for this repository (across all sessions).",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string", "description": "Repository identifier (URL or path)."}
                },
                "required": ["repo_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_past_sessions",
            "description": "List past research sessions for this repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string", "description": "Repository identifier (URL or path)."}
                },
                "required": ["repo_url"],
            },
        },
    },
]


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _execute_tool(
    *,
    name: str,
    arguments: dict[str, Any],
    root: Path,
    session_id: int,
    repo_identifier: str,
) -> str:
    try:
        if name == "list_files":
            path = arguments.get("path") or "."
            result = filesystem_tools.list_files(root, path)
        elif name == "read_file":
            result = filesystem_tools.read_file(
                root,
                arguments["path"],
                arguments.get("start_line"),
                arguments.get("end_line"),
            )
        elif name == "search_code":
            result = filesystem_tools.search_code(
                root,
                arguments["query"],
                arguments.get("glob_pattern") or "**/*",
            )
        elif name == "get_file_summary":
            result = filesystem_tools.get_file_summary(root, arguments["path"])
        elif name == "save_finding":
            sid = int(arguments.get("session_id") or session_id)
            result = db_tools.save_finding(
                sid,
                str(arguments.get("file_path") or ""),
                str(arguments.get("note") or ""),
            )
        elif name == "get_previous_findings":
            url = str(arguments.get("repo_url") or repo_identifier)
            result = db_tools.get_previous_findings(url)
        elif name == "list_past_sessions":
            url = str(arguments.get("repo_url") or repo_identifier)
            result = db_tools.list_past_sessions(url)
        else:
            result = {"error": f"unknown tool: {name}"}
    except Exception as e:
        result = {"error": type(e).__name__, "detail": str(e)}
    return _json_dumps(result)


def _split_answer_and_references(text: str) -> tuple[str, list[dict[str, Any]]]:
    marker = "REFERENCES_JSON="
    idx = text.rfind(marker)
    if idx == -1:
        return text.strip(), []
    prefix = text[:idx].strip()
    suffix = text[idx + len(marker):].strip()
    try:
        refs, _ = json.JSONDecoder().raw_decode(suffix)
    except json.JSONDecodeError:
        return text.strip(), []
    if not isinstance(refs, list):
        return prefix, []
    return prefix, refs


@dataclass
class RunResult:
    final_answer: str
    references: list[dict[str, Any]]
    input_tokens: int | None
    output_tokens: int | None


_SYSTEM_INSTRUCTION = (
    "You are a senior backend engineer researching a codebase. "
    "You must use tools to inspect the repository; do not invent file paths. "
    "Start by checking prior sessions/findings for this repo when helpful. "
    "Use save_finding to record durable intermediate conclusions tied to files. "
    "When you can answer the user's question with evidence, stop calling tools and "
    "write the final answer in clear technical prose with inline file/line mentions. "
    "After the answer, on its own last line, output REFERENCES_JSON= followed by a JSON array. "
    "Each item should be an object with keys: file (relative path), start_line (optional int), "
    "end_line (optional int), note (short string)."
)


def run_session(session_id: int) -> RunResult:
    session = ResearchSession.objects.select_related("repository").get(pk=session_id)
    if session.status == ResearchSession.Status.RUNNING:
        raise RuntimeError("session already running")

    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    repo: Repository = session.repository
    root = Path(session.checkout_path)
    if not root.exists():
        raise RuntimeError("checkout path missing; cannot run agent")

    session.status = ResearchSession.Status.RUNNING
    session.error_message = ""
    session.save(update_fields=["status", "error_message", "updated_at"])

    client = Groq(api_key=settings.GROQ_API_KEY)
    model_name = settings.GROQ_MODEL

    prior = db_tools.get_previous_findings(repo.identifier)
    past = db_tools.list_past_sessions(repo.identifier)

    initial_text = (
        f"Repository identifier: {repo.identifier}\n"
        f"Checkout root on disk: {root}\n"
        f"Current session_id (for save_finding): {session.id}\n\n"
        f"Question:\n{session.question}\n\n"
        f"Context snapshot (DB):\n"
        f"prior_findings={_json_dumps(prior)}\n"
        f"past_sessions={_json_dumps(past)}\n"
    )

    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM_INSTRUCTION},
        {"role": "user", "content": initial_text},
    ]

    total_input = 0
    total_output = 0
    max_rounds = settings.AGENT_MAX_TOOL_ROUNDS

    # [MOMIN] Three exit paths from this loop (design decision):
    # [MOMIN]   EXIT 1 — model returns text-only (no tool_calls): happy path, COMPLETED.
    # [MOMIN]   EXIT 2 — loop exhausts max_rounds: session FAILED, bill capped.
    # [MOMIN]   EXIT 3 — any exception: caught by the view, session FAILED.
    # [MOMIN] The hard round cap also prevents infinite loops — the model always
    # [MOMIN] receives new tool results each iteration so it cannot spin on the same
    # [MOMIN] state, and the cap ensures a worst-case bound on Groq API spend.
    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=_TOOL_DECLARATIONS,
            tool_choice="auto",
            temperature=0.0,
        )

        usage = response.usage
        if usage:
            total_input += usage.prompt_tokens or 0
            total_output += usage.completion_tokens or 0

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        tool_calls = message.tool_calls or []

        if tool_calls:
            for tc in tool_calls:
                name = tc.function.name
                try:
                    arguments = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}

                if name == "save_finding" and "session_id" not in arguments:
                    arguments["session_id"] = session.id

                tool_output = _execute_tool(
                    name=name,
                    arguments=arguments,
                    root=root,
                    session_id=session.id,
                    repo_identifier=repo.identifier,
                )
                # [MOMIN] Tool call is logged BEFORE the result feeds back into
                # [MOMIN] the conversation. If the runner crashes mid-run the DB
                # [MOMIN] still holds the complete log up to that point.
                db_tools.log_tool_call(session.id, name, arguments, tool_output)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_output,
                })
            continue

        final_text = (message.content or "").strip()
        answer, refs = _split_answer_and_references(final_text)

        repo.last_analyzed_at = timezone.now()
        repo.save(update_fields=["last_analyzed_at"])

        session.final_answer = answer
        session.references_json = refs
        session.status = ResearchSession.Status.COMPLETED
        session.input_tokens = total_input or None
        session.output_tokens = total_output or None
        session.save(
            update_fields=[
                "final_answer",
                "references_json",
                "status",
                "input_tokens",
                "output_tokens",
                "updated_at",
            ]
        )
        return RunResult(
            final_answer=answer,
            references=refs,
            input_tokens=total_input or None,
            output_tokens=total_output or None,
        )

    session.status = ResearchSession.Status.FAILED
    session.error_message = f"Stopped: exceeded AGENT_MAX_TOOL_ROUNDS={max_rounds}"
    session.save(update_fields=["status", "error_message", "updated_at"])
    raise RuntimeError(session.error_message)

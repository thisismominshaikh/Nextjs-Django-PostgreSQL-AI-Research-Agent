"""Database tools exposed to the agent (Django ORM only)."""
# [AI] Future annotations for PEP 604 union syntax on older Python.
from __future__ import annotations

from research.models import Finding, Repository, ResearchSession, ToolCallLog


def save_finding(session_id: int, file_path: str, note: str) -> dict:
    # [MOMIN] We look the session up rather than trusting the id blindly so a
    # [MOMIN] mis-routed tool call cannot silently create orphan findings. The
    # [MOMIN] return shape mirrors the rest of the tool API: {ok, ...}.
    session = ResearchSession.objects.filter(pk=session_id).first()
    if not session:
        return {"ok": False, "error": "session not found"}
    f = Finding.objects.create(session=session, file_path=file_path or "", note=note)
    return {"ok": True, "finding_id": f.id}


def get_previous_findings(repo_url: str) -> dict:
    # [AI] Lookup repo by normalized identifier; return empty if unseen.
    repo = Repository.objects.filter(identifier=repo_url.strip()).first()
    if not repo:
        return {"repository_found": False, "findings": []}
    # [MOMIN] We cap at 50 most-recent findings (across all sessions) and use
    # [MOMIN] select_related on `session` to avoid an N+1 when reading the
    # [MOMIN] question text on each finding for the model context.
    qs = (
        Finding.objects.filter(session__repository=repo)
        .select_related("session")
        .order_by("-session__created_at", "-id")[:50]
    )
    # [MOMIN] Question and note are truncated here — these payloads are read by
    # [MOMIN] the LLM and bytes are dollars. The truncation is conservative
    # [MOMIN] enough to keep notes useful while bounding prompt size.
    findings = [
        {
            "session_id": f.session_id,
            "question": f.session.question[:500],
            "file_path": f.file_path,
            "note": f.note[:2000],
            "created_at": f.created_at.isoformat(),
        }
        for f in qs
    ]
    return {"repository_found": True, "findings": findings}


def list_past_sessions(repo_url: str, limit: int = 20) -> dict:
    # [AI] List recent sessions for the given repo identifier.
    repo = Repository.objects.filter(identifier=repo_url.strip()).first()
    if not repo:
        return {"repository_found": False, "sessions": []}
    # [MOMIN] `.values()` keeps this query lightweight — we only ship a preview
    # [MOMIN] of the answer, never the full body, into the agent context.
    sessions = (
        ResearchSession.objects.filter(repository=repo)
        .order_by("-created_at")[:limit]
        .values("id", "question", "status", "created_at", "final_answer")
    )
    rows = []
    for s in sessions:
        rows.append(
            {
                "id": s["id"],
                "question": s["question"][:500],
                "status": s["status"],
                "created_at": s["created_at"].isoformat() if s["created_at"] else None,
                "answer_preview": (s["final_answer"] or "")[:400],
            }
        )
    return {"repository_found": True, "sessions": rows}


def log_tool_call(
    session_id: int,
    tool_name: str,
    arguments: dict,
    result_excerpt: str,
    max_excerpt: int = 8000,
) -> None:
    # [MOMIN] Result excerpts are hard-capped here (8 KB by default) so a single
    # [MOMIN] huge tool result cannot blow up the database row size. The ellipsis
    # [MOMIN] is intentional — it visually flags truncation when reading the log.
    excerpt = result_excerpt if len(result_excerpt) <= max_excerpt else result_excerpt[:max_excerpt] + "…"
    ToolCallLog.objects.create(
        session_id=session_id,
        tool_name=tool_name,
        arguments=arguments or {},
        result_excerpt=excerpt,
    )

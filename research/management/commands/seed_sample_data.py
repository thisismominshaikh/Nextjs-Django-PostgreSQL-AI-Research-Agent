"""
Management command: seed_sample_data

Creates realistic sample records in the database showing what the agent
produces after a real run. Run after migrations:

    python manage.py seed_sample_data
    python manage.py seed_sample_data --clear   # wipe and re-seed
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone


SAMPLE_DATA = [
    {
        "repo": {
            "identifier": "https://github.com/tiangolo/fastapi",
            "display_name": "fastapi",
        },
        "sessions": [
            {
                "question": "How does FastAPI handle dependency injection internally?",
                "final_answer": (
                    "FastAPI's dependency injection system is implemented in `fastapi/dependencies/utils.py`. "
                    "The entry point is `solve_dependencies()` (line ~200), which recursively resolves "
                    "the dependency graph for each endpoint at request time.\n\n"
                    "Each path operation function's parameters are inspected via "
                    "`get_typed_signature()` in `fastapi/utils.py`. Parameters annotated with "
                    "`Depends(...)` are collected into a `Dependant` dataclass "
                    "(`fastapi/dependencies/models.py`). The `Dependant` object stores the callable, "
                    "its sub-dependencies, path/query/body/header/cookie fields, and security schemes.\n\n"
                    "During a request, `solve_dependencies()` walks the tree depth-first, calling each "
                    "dependency callable (which may itself be an async function or a generator). "
                    "Generator dependencies (using `yield`) are treated as context managers — FastAPI "
                    "collects them and calls `finally` blocks after the response is sent, enabling "
                    "clean resource teardown (e.g., closing a database session).\n\n"
                    "Caching is applied per-request by default: if the same dependency appears multiple "
                    "times in the graph, it is solved only once and its result is reused "
                    "(`use_cache=True` on `Depends`).\n\n"
                    "REFERENCES_JSON=[{\"file\": \"fastapi/dependencies/utils.py\", \"start_line\": 195, \"end_line\": 310, \"note\": \"solve_dependencies() — core resolution loop\"}, {\"file\": \"fastapi/dependencies/models.py\", \"start_line\": 1, \"end_line\": 60, \"note\": \"Dependant dataclass definition\"}, {\"file\": \"fastapi/utils.py\", \"start_line\": 40, \"end_line\": 80, \"note\": \"get_typed_signature() — parameter introspection\"}]"
                ),
                "references_json": [
                    {"file": "fastapi/dependencies/utils.py", "start_line": 195, "end_line": 310, "note": "solve_dependencies() — core resolution loop"},
                    {"file": "fastapi/dependencies/models.py", "start_line": 1, "end_line": 60, "note": "Dependant dataclass definition"},
                    {"file": "fastapi/utils.py", "start_line": 40, "end_line": 80, "note": "get_typed_signature() — parameter introspection"},
                ],
                "input_tokens": 14820,
                "output_tokens": 612,
                "findings": [
                    {"file_path": "fastapi/dependencies/utils.py", "note": "solve_dependencies() at line ~200 is the main DI resolution entry point. It calls itself recursively for sub-dependencies."},
                    {"file_path": "fastapi/dependencies/models.py", "note": "Dependant dataclass holds path_params, query_params, body_fields, dependencies list, and security_requirements."},
                    {"file_path": "fastapi/utils.py", "note": "get_typed_signature() uses inspect.signature + typing.get_type_hints to extract annotated parameter info."},
                    {"file_path": "fastapi/dependencies/utils.py", "note": "Generator dependencies are wrapped with contextlib and finalized in a background task after response dispatch."},
                ],
                "tool_calls": [
                    {"tool_name": "list_past_sessions", "arguments": {"repo_url": "https://github.com/tiangolo/fastapi"}, "result_excerpt": "{\"repository_found\": false, \"sessions\": []}"},
                    {"tool_name": "list_files", "arguments": {"path": "."}, "result_excerpt": "{\"entries\": [{\"path\": \"fastapi\", \"type\": \"dir\"}, {\"path\": \"tests\", \"type\": \"dir\"}, {\"path\": \"README.md\", \"type\": \"file\"}]}"},
                    {"tool_name": "list_files", "arguments": {"path": "fastapi"}, "result_excerpt": "{\"entries\": [{\"path\": \"fastapi/dependencies\", \"type\": \"dir\"}, {\"path\": \"fastapi/routing.py\", \"type\": \"file\"}, {\"path\": \"fastapi/utils.py\", \"type\": \"file\"}]}"},
                    {"tool_name": "search_code", "arguments": {"query": "solve_dependencies", "glob_pattern": "**/*.py"}, "result_excerpt": "{\"match_count\": 12, \"matches\": [{\"path\": \"fastapi/dependencies/utils.py\", \"line\": 201, \"snippet\": \"async def solve_dependencies(\"}]}"},
                    {"tool_name": "read_file", "arguments": {"path": "fastapi/dependencies/utils.py", "start_line": 195, "end_line": 260}, "result_excerpt": "195|async def solve_dependencies(\n196|    *,\n197|    request: Union[Request, WebSocket],\n..."},
                    {"tool_name": "get_file_summary", "arguments": {"path": "fastapi/dependencies/models.py"}, "result_excerpt": "{\"path\": \"fastapi/dependencies/models.py\", \"total_lines\": 64, \"structure_hints\": [\"L1: class Dependant:\"]}"},
                    {"tool_name": "save_finding", "arguments": {"session_id": 1, "file_path": "fastapi/dependencies/utils.py", "note": "solve_dependencies() at line ~200 is the main DI resolution entry point."}, "result_excerpt": "{\"ok\": true, \"finding_id\": 1}"},
                ],
            },
            {
                "question": "Where are HTTP exception handlers registered and how do they work?",
                "final_answer": (
                    "HTTP exception handling in FastAPI is layered across Starlette and FastAPI itself.\n\n"
                    "The base handler lives in `starlette/exceptions.py` as `HTTPException`. FastAPI "
                    "re-exports this in `fastapi/exceptions.py` and adds its own `RequestValidationError`.\n\n"
                    "In `fastapi/applications.py`, the `FastAPI.__init__()` method calls "
                    "`self.add_exception_handler(HTTPException, http_exception_handler)` and "
                    "`self.add_exception_handler(RequestValidationError, request_validation_exception_handler)`. "
                    "These default handlers return JSON responses with appropriate status codes.\n\n"
                    "Custom handlers can be registered via `@app.exception_handler(MyException)` decorator "
                    "or `app.add_exception_handler(MyException, handler_func)`. Starlette's middleware "
                    "stack catches exceptions during request dispatch and routes them to the registered "
                    "handler based on exception type matching (exact class or parent class).\n\n"
                    "REFERENCES_JSON=[{\"file\": \"fastapi/applications.py\", \"start_line\": 60, \"end_line\": 120, \"note\": \"FastAPI.__init__ registers default exception handlers\"}, {\"file\": \"fastapi/exception_handlers.py\", \"start_line\": 1, \"end_line\": 30, \"note\": \"Default http_exception_handler and validation_exception_handler\"}, {\"file\": \"fastapi/exceptions.py\", \"start_line\": 1, \"end_line\": 20, \"note\": \"FastAPI's exception classes\"}]"
                ),
                "references_json": [
                    {"file": "fastapi/applications.py", "start_line": 60, "end_line": 120, "note": "FastAPI.__init__ registers default exception handlers"},
                    {"file": "fastapi/exception_handlers.py", "start_line": 1, "end_line": 30, "note": "Default http_exception_handler and validation_exception_handler"},
                    {"file": "fastapi/exceptions.py", "start_line": 1, "end_line": 20, "note": "FastAPI's exception classes"},
                ],
                "input_tokens": 9340,
                "output_tokens": 480,
                "findings": [
                    {"file_path": "fastapi/applications.py", "note": "Default exception handlers are registered in FastAPI.__init__ via add_exception_handler."},
                    {"file_path": "fastapi/exception_handlers.py", "note": "http_exception_handler returns JSONResponse; request_validation_exception_handler returns 422 with error details."},
                ],
                "tool_calls": [
                    {"tool_name": "get_previous_findings", "arguments": {"repo_url": "https://github.com/tiangolo/fastapi"}, "result_excerpt": "{\"repository_found\": true, \"findings\": [{\"file_path\": \"fastapi/dependencies/utils.py\", \"note\": \"solve_dependencies()...\"}]}"},
                    {"tool_name": "search_code", "arguments": {"query": "add_exception_handler", "glob_pattern": "fastapi/**/*.py"}, "result_excerpt": "{\"match_count\": 8, \"matches\": [{\"path\": \"fastapi/applications.py\", \"line\": 95, \"snippet\": \"self.add_exception_handler(HTTPException, http_exception_handler)\"}]}"},
                    {"tool_name": "read_file", "arguments": {"path": "fastapi/applications.py", "start_line": 60, "end_line": 130}, "result_excerpt": "60|class FastAPI(Starlette):\n..."},
                    {"tool_name": "save_finding", "arguments": {"session_id": 2, "file_path": "fastapi/applications.py", "note": "Default exception handlers registered in __init__."}, "result_excerpt": "{\"ok\": true, \"finding_id\": 5}"},
                ],
            },
        ],
    },
    {
        "repo": {
            "identifier": "https://github.com/celery/celery",
            "display_name": "celery",
        },
        "sessions": [
            {
                "question": "Where is task retry logic implemented, and what backoff strategies are supported?",
                "final_answer": (
                    "Task retry logic in Celery is primarily implemented in `celery/app/task.py`, "
                    "inside the `Task.retry()` method (approximately line 680–780).\n\n"
                    "The `retry()` method accepts these key parameters:\n"
                    "- `exc`: the exception that triggered the retry (used to re-raise on final failure)\n"
                    "- `countdown`: fixed delay in seconds before the next attempt\n"
                    "- `eta`: absolute datetime for the next attempt\n"
                    "- `max_retries`: override the task-level `max_retries` attribute\n"
                    "- `throw`: if True (default), raises `Retry` to signal the worker\n\n"
                    "**Backoff strategies**: Celery does not ship a built-in exponential backoff helper "
                    "in the core retry path. Instead, callers compute `countdown` themselves:\n\n"
                    "```python\n"
                    "self.retry(exc=exc, countdown=2 ** self.request.retries)\n"
                    "```\n\n"
                    "The `celery.utils.functional` module provides `maybe_list` and similar utilities, "
                    "but no backoff primitives. Third-party packages like `celery-retry-on` or manual "
                    "exponential formulas in the task body are the standard pattern.\n\n"
                    "The `Retry` exception class is defined in `celery/exceptions.py` and carries the "
                    "retry ETA/countdown and original exception for logging purposes.\n\n"
                    "REFERENCES_JSON=[{\"file\": \"celery/app/task.py\", \"start_line\": 680, \"end_line\": 780, \"note\": \"Task.retry() implementation\"}, {\"file\": \"celery/exceptions.py\", \"start_line\": 80, \"end_line\": 110, \"note\": \"Retry exception class\"}, {\"file\": \"celery/app/task.py\", \"start_line\": 1, \"end_line\": 50, \"note\": \"Task class attributes including max_retries default\"}]"
                ),
                "references_json": [
                    {"file": "celery/app/task.py", "start_line": 680, "end_line": 780, "note": "Task.retry() implementation"},
                    {"file": "celery/exceptions.py", "start_line": 80, "end_line": 110, "note": "Retry exception class"},
                    {"file": "celery/app/task.py", "start_line": 1, "end_line": 50, "note": "Task class attributes including max_retries default"},
                ],
                "input_tokens": 18200,
                "output_tokens": 720,
                "findings": [
                    {"file_path": "celery/app/task.py", "note": "Task.retry() at line ~680. Accepts countdown (fixed delay), eta (absolute time), max_retries override, and exc to chain."},
                    {"file_path": "celery/exceptions.py", "note": "Retry exception (line ~80) holds the message, when (eta), exc, and is caught by the worker to reschedule."},
                    {"file_path": "celery/app/task.py", "note": "No built-in exponential backoff — callers use: self.retry(exc=exc, countdown=2**self.request.retries)"},
                ],
                "tool_calls": [
                    {"tool_name": "list_files", "arguments": {"path": "."}, "result_excerpt": "{\"entries\": [{\"path\": \"celery\", \"type\": \"dir\"}, {\"path\": \"docs\", \"type\": \"dir\"}]}"},
                    {"tool_name": "search_code", "arguments": {"query": "def retry", "glob_pattern": "celery/**/*.py"}, "result_excerpt": "{\"matches\": [{\"path\": \"celery/app/task.py\", \"line\": 683, \"snippet\": \"def retry(self, args=None, kwargs=None, exc=None,\"}]}"},
                    {"tool_name": "read_file", "arguments": {"path": "celery/app/task.py", "start_line": 680, "end_line": 780}, "result_excerpt": "680|def retry(self, args=None, kwargs=None, exc=None, throw=True,\n681|           eta=None, countdown=None, max_retries=None, **options):"},
                    {"tool_name": "search_code", "arguments": {"query": "class Retry", "glob_pattern": "celery/**/*.py"}, "result_excerpt": "{\"matches\": [{\"path\": \"celery/exceptions.py\", \"line\": 82, \"snippet\": \"class Retry(Exception):\"}]}"},
                    {"tool_name": "save_finding", "arguments": {"session_id": 3, "file_path": "celery/app/task.py", "note": "Task.retry() at line ~680. countdown and eta are the two timing modes."}, "result_excerpt": "{\"ok\": true, \"finding_id\": 8}"},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with realistic sample agent-run records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing data before seeding.",
        )

    def handle(self, *args, **options):
        from research.models import Finding, Repository, ResearchSession, ToolCallLog

        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            ToolCallLog.objects.all().delete()
            Finding.objects.all().delete()
            ResearchSession.objects.all().delete()
            Repository.objects.all().delete()
            self.stdout.write(self.style.WARNING("  Cleared all records."))

        now = timezone.now()
        session_counter = 0
        finding_counter = 0
        tool_counter = 0

        for repo_data in SAMPLE_DATA:
            repo, created = Repository.objects.get_or_create(
                identifier=repo_data["repo"]["identifier"],
                defaults={"display_name": repo_data["repo"]["display_name"]},
            )
            action = "Created" if created else "Found existing"
            self.stdout.write(f"  {action} repo: {repo.display_name}")

            for i, sess_data in enumerate(repo_data["sessions"]):
                # Space sessions out in time for realistic ordering
                import datetime
                session_time = now - datetime.timedelta(hours=(len(repo_data["sessions"]) - i) * 3)

                session = ResearchSession.objects.create(
                    repository=repo,
                    question=sess_data["question"],
                    final_answer=sess_data["final_answer"],
                    references_json=sess_data["references_json"],
                    status=ResearchSession.Status.COMPLETED,
                    checkout_path="",  # No disk path for sample data
                    input_tokens=sess_data.get("input_tokens"),
                    output_tokens=sess_data.get("output_tokens"),
                )
                # Override auto timestamps using update() to bypass auto_now_add
                ResearchSession.objects.filter(pk=session.pk).update(
                    created_at=session_time, updated_at=session_time
                )
                session_counter += 1

                # Create findings
                for f_data in sess_data.get("findings", []):
                    Finding.objects.create(
                        session=session,
                        file_path=f_data["file_path"],
                        note=f_data["note"],
                    )
                    finding_counter += 1

                # Create tool call logs
                for t_data in sess_data.get("tool_calls", []):
                    ToolCallLog.objects.create(
                        session=session,
                        tool_name=t_data["tool_name"],
                        arguments=t_data["arguments"],
                        result_excerpt=t_data["result_excerpt"],
                    )
                    tool_counter += 1

            # Update repo's last_analyzed_at to the most recent session time
            repo.last_analyzed_at = now - datetime.timedelta(hours=3)
            repo.save(update_fields=["last_analyzed_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeding complete:\n"
                f"  Repositories : {len(SAMPLE_DATA)}\n"
                f"  Sessions     : {session_counter}\n"
                f"  Findings     : {finding_counter}\n"
                f"  Tool calls   : {tool_counter}\n\n"
                f"Run the server and visit /api/repositories/ to see the data."
            )
        )

"""Django REST Framework views for the Codebase Research Agent API."""
from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from research.agent.grok_runner import run_session
from research.models import Finding, Repository, ResearchSession
from research.serializers import (
    FindingSerializer,
    RepositorySerializer,
    ResearchSessionDetailSerializer,
    ResearchSessionSerializer,
    StartResearchSessionSerializer,
)
from research.services.git_clone import ensure_repo_checkout


def root_index(request):
    """GET / — discovery document listing all available API endpoints."""
    return JsonResponse(
        {
            "service": "codebase-research-agent",
            "llm": "Groq",
            "api_base": "/api/",
            "paths": {
                "admin": "/admin/",
                "list_all_sessions": "GET  /api/sessions/?status=<status>&limit=<n>",
                "start_session":     "POST /api/sessions/start/",
                "session_detail":    "GET  /api/sessions/<id>/",
                "session_findings":  "GET  /api/sessions/<id>/findings/",
                "repo_sessions":     "GET  /api/repositories/sessions/?repo_url=<url>",
                "list_repositories": "GET  /api/repositories/",
            },
            "hint": 'POST JSON to /api/sessions/start/ with "repo_url" and "question".',
        }
    )


@method_decorator(csrf_exempt, name="dispatch")
class StartResearchSessionView(APIView):
    """
    POST /api/sessions/start/

    Body (JSON):
        { "repo_url": "https://github.com/owner/repo", "question": "How does X work?" }

    Clones or resolves the repo, runs the Groq agent synchronously, and
    returns the completed (or failed) session record.
    """

    def post(self, request):
        ser = StartResearchSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        repo_url = ser.validated_data["repo_url"]
        question = ser.validated_data["question"]

        try:
            identifier, path = ensure_repo_checkout(repo_url)
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"detail": f"Repository checkout failed: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        repo, _ = Repository.objects.get_or_create(
            identifier=identifier,
            defaults={"display_name": identifier.rsplit("/", 1)[-1].replace(".git", "")},
        )

        session = ResearchSession.objects.create(
            repository=repo,
            question=question,
            checkout_path=str(path),
            status=ResearchSession.Status.PENDING,
        )

        try:
            run_session(session.id)
        except Exception as exc:  # noqa: BLE001
            session.refresh_from_db()
            if session.status != ResearchSession.Status.COMPLETED:
                session.status = ResearchSession.Status.FAILED
                session.error_message = str(exc)
                session.save(update_fields=["status", "error_message", "updated_at"])
            return Response(
                ResearchSessionSerializer(session).data,
                status=status.HTTP_200_OK,
            )

        session.refresh_from_db()
        return Response(ResearchSessionSerializer(session).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class ResearchSessionDetailView(APIView):
    """
    GET /api/sessions/<id>/

    Returns full session detail including findings and tool call log.
    """

    def get(self, request, pk: int):
        session = get_object_or_404(
            ResearchSession.objects.select_related("repository").prefetch_related(
                "findings", "tool_calls"
            ),
            pk=pk,
        )
        return Response(ResearchSessionDetailSerializer(session).data)


@method_decorator(csrf_exempt, name="dispatch")
class ListPastSessionsView(APIView):
    """
    GET /api/repositories/sessions/?repo_url=<url>

    Returns all sessions for a given repository identifier.
    """

    def get(self, request):
        repo_url = request.query_params.get("repo_url")
        if not repo_url:
            return Response(
                {"detail": "repo_url query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        repo = Repository.objects.filter(identifier=repo_url.strip()).first()
        if not repo:
            return Response(
                {"repository": None, "sessions": []},
                status=status.HTTP_200_OK,
            )
        sessions = (
            ResearchSession.objects.filter(repository=repo)
            .select_related("repository")
            .order_by("-created_at")[:50]
        )
        return Response(
            {
                "repository": RepositorySerializer(repo).data,
                "sessions": ResearchSessionSerializer(sessions, many=True).data,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ListRepositoriesView(APIView):
    """
    GET /api/repositories/

    Returns all repositories that have been analyzed, ordered by most recent.
    Supports optional ?search=<str> query parameter to filter by identifier.
    """

    def get(self, request):
        qs = Repository.objects.all().order_by("-last_analyzed_at", "-id")
        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(identifier__icontains=search)
        repos = list(qs[:100])
        return Response(
            {
                "count": len(repos),
                "repositories": RepositorySerializer(repos, many=True).data,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class SessionFindingsView(APIView):
    """
    GET /api/sessions/<id>/findings/

    Returns all agent-authored findings for a specific session.
    """

    def get(self, request, pk: int):
        session = get_object_or_404(ResearchSession, pk=pk)
        findings = Finding.objects.filter(session=session).order_by("created_at")
        return Response(
            {
                "session_id": session.id,
                "question": session.question,
                "status": session.status,
                "finding_count": findings.count(),
                "findings": FindingSerializer(findings, many=True).data,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ListAllSessionsView(APIView):
    """
    GET /api/sessions/

    Returns all research sessions across all repositories, ordered by most
    recent. Supports optional ?status=<status> and ?limit=<n> query params.
    """

    def get(self, request):
        qs = (
            ResearchSession.objects.select_related("repository")
            .order_by("-created_at")
        )
        status_filter = request.query_params.get("status", "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        try:
            limit = min(int(request.query_params.get("limit", "100")), 500)
        except (ValueError, TypeError):
            limit = 100
        sessions = list(qs[:limit])
        return Response(
            {
                "count": len(sessions),
                "sessions": ResearchSessionSerializer(sessions, many=True).data,
            }
        )

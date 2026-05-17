"""URL patterns for the research app — mounted at /api/ by config/urls.py."""
from django.urls import re_path

from research import views

urlpatterns = [
    # List all sessions across all repositories (GET, optional ?status= ?limit=)
    re_path(r"^sessions/?$", views.ListAllSessionsView.as_view(), name="session-list"),
    # Start a new research session (POST)
    re_path(r"^sessions/start/?$", views.StartResearchSessionView.as_view(), name="session-start"),
    # Retrieve a session with its findings and tool-call log (GET)
    re_path(r"^sessions/(?P<pk>\d+)/?$", views.ResearchSessionDetailView.as_view(), name="session-detail"),
    # List findings for a specific session (GET)
    re_path(r"^sessions/(?P<pk>\d+)/findings/?$", views.SessionFindingsView.as_view(), name="session-findings"),
    # List all past sessions for a repository (GET ?repo_url=...)
    re_path(r"^repositories/sessions/?$", views.ListPastSessionsView.as_view(), name="repo-sessions"),
    # List all repositories that have been analyzed (GET)
    re_path(r"^repositories/?$", views.ListRepositoriesView.as_view(), name="repo-list"),
]

"""URL configuration."""
# [AI] Root URLConf — wires admin, the API app, and the discovery index.
from django.contrib import admin
from django.urls import include, path

from research.views import root_index

# [MOMIN] The API is intentionally namespaced under `/api/` so the Next.js
# [MOMIN] proxy can forward `/proxy-api/*` -> `/api/*` without touching admin
# [MOMIN] or the discovery index. Keeping `root_index` at "/" gives reviewers
# [MOMIN] a self-describing entry point without needing OpenAPI tooling.
urlpatterns = [
    # [AI] Discovery document for humans hitting the bare host.
    path("", root_index),
    # [AI] Django admin — useful for inspecting sessions/findings during a demo.
    path("admin/", admin.site.urls),
    # [MOMIN] All public REST endpoints live behind the `research` app's URLConf.
    path("api/", include("research.urls")),
]

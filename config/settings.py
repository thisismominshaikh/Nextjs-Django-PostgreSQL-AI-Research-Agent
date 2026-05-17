"""Django settings for CodeFusion-style codebase research agent."""
# [AI] Standard imports + .env loading for local development.
import os
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# [MOMIN] SECRET_KEY ships a clearly-fake default so a missing env var fails loud
# [MOMIN] in code review rather than silently in production. The string itself is
# [MOMIN] a billboard reminder ("change-me-in-production-not-for-prod").
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "dev-only-change-me-in-production-not-for-prod"
)

# [AI] DEBUG is on by default for local dev; disable via env in production.
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in ("1", "true", "yes")

# [AI] Comma-separated host list parsed from env (defaults to localhost).
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# [AI] Standard Django + DRF + project app registration.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "research",
]

# [AI] Default Django middleware stack — corsheaders must come before CommonMiddleware.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# [MOMIN] CORS: allow the Next.js dev server and any configured frontend origin.
# In production set CORS_ALLOWED_ORIGINS via env; in development we allow all.
_cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if _cors_origins:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]
else:
    # Development default: allow Next.js default ports.
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
CORS_ALLOW_CREDENTIALS = False

ROOT_URLCONF = "config.urls"

# [AI] Default template config (admin uses it; the app itself returns JSON).
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# DATABASE_URL takes a full postgres connection string, e.g.:
# postgresql://user:password@host:port/dbname
# Falls back to SQLite for local dev when DATABASE_URL is not set.
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url:
    _u = urllib.parse.urlparse(_db_url)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _u.path.lstrip("/"),
            "USER": _u.username,
            "PASSWORD": _u.password,
            "HOST": _u.hostname,
            "PORT": _u.port or 5432,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# [AI] Default password validators — admin only; API has no user auth today.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# [AI] i18n / tz defaults — UTC everywhere keeps the audit log unambiguous.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
# Required by collectstatic (run as a preDeployCommand on Railway). Without
# this setting Django raises ImproperlyConfigured before writing a single file.
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# [MOMIN] DRF is locked down to JSON in/out only. Browsable API and form parsers
# [MOMIN] are intentionally disabled — this is a backend service consumed by a
# [MOMIN] Next.js frontend; we don't want HTML to ever leak from `/api/*`.
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

# [MOMIN] Repo cache lives outside BASE_DIR by default in production but defaults
# [MOMIN] to `<project>/repo_workdir` for development. We `mkdir(parents=True)` at
# [MOMIN] import time so the first session-start request never has to handle a
# [MOMIN] missing-directory race.
REPO_WORKDIR = Path(os.environ.get("REPO_WORKDIR", str(BASE_DIR / "repo_workdir")))
REPO_WORKDIR.mkdir(parents=True, exist_ok=True)

# [MOMIN] Three explicit safety knobs for the agent. Each one bounds a distinct
# [MOMIN] cost axis: ROUNDS bounds API spend, READ_FILE_MAX_CHARS bounds prompt
# [MOMIN] size, SEARCH_MAX_MATCHES bounds latency. All are env-overridable.
AGENT_MAX_TOOL_ROUNDS = int(os.environ.get("AGENT_MAX_TOOL_ROUNDS", "24"))
AGENT_READ_FILE_MAX_CHARS = int(os.environ.get("AGENT_READ_FILE_MAX_CHARS", "120000"))
AGENT_SEARCH_MAX_MATCHES = int(os.environ.get("AGENT_SEARCH_MAX_MATCHES", "40"))

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

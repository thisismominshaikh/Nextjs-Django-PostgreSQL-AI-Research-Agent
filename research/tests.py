from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from research.services.filesystem_tools import list_files, read_file
from research.services.git_clone import normalize_repo_identifier


class RootIndexTests(TestCase):
    def test_root_returns_json(self):
        r = Client().get("/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["api_base"], "/api/")
        self.assertIn("start_session", data["paths"])


class GitHelpersTests(TestCase):
    def test_normalize_identifier(self):
        self.assertEqual(normalize_repo_identifier("  https://x/y  "), "https://x/y")


class FilesystemToolsTests(TestCase):
    def test_list_and_read_self_project(self):
        from pathlib import Path
        from django.conf import settings

        root = Path(settings.BASE_DIR)
        listed = list_files(root, ".")
        self.assertIn("entries", listed)
        self.assertFalse(listed.get("truncated", False))
        sample = read_file(root, "manage.py", 1, 5)
        self.assertIn("total_lines", sample)
        self.assertIn("1|", sample["content"])


class StartSessionValidationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_start_requires_fields(self):
        url = reverse("session-start")
        r = self.client.post(url, {}, format="json")
        self.assertEqual(r.status_code, 400)


class ListPastSessionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_requires_repo_url(self):
        url = reverse("repo-sessions")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 400)

    def test_list_empty_for_unknown_repo(self):
        url = reverse("repo-sessions")
        r = self.client.get(url, {"repo_url": "https://example.com/none/none"})
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.data["repository"])
        self.assertEqual(r.data["sessions"], [])

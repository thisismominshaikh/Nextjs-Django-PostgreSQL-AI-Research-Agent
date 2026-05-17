# [AI] Standard Django ORM imports.
from django.db import models


class Repository(models.Model):
    """A GitHub URL or local path identity we analyze."""

    # [MOMIN] `identifier` is the normalized repo URL or absolute local path and is
    # [MOMIN] the natural key. Marking it unique lets us rely on get_or_create in
    # [MOMIN] the start-session view, and prevents duplicate Repository rows when
    # [MOMIN] the same URL is submitted from different sessions.
    identifier = models.CharField(
        max_length=2048,
        unique=True,
        help_text="Normalized repo URL or absolute local path",
    )
    # [AI] Human-friendly label derived from the identifier (last path segment).
    display_name = models.CharField(max_length=512, blank=True)
    # [AI] Bumped by the agent runner on every successful completion.
    last_analyzed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # [MOMIN] Default ordering puts the most recently analyzed repos first —
        # [MOMIN] this is the order the admin and any future list view will use.
        ordering = ["-last_analyzed_at", "-id"]

    def __str__(self) -> str:
        return self.display_name or self.identifier[:80]


class ResearchSession(models.Model):
    """One question run against a repository."""

    # [MOMIN] Status is modeled as TextChoices (not a separate job table) because
    # [MOMIN] sessions are run synchronously today. A dedicated job model would
    # [MOMIN] only become necessary if/when execution moves to a worker queue.
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    # [AI] FK to Repository with cascade so deleting a repo cleans up its history.
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    question = models.TextField()
    final_answer = models.TextField(blank=True)
    # [MOMIN] References are stored as JSON (not a child table) because they are
    # [MOMIN] always read whole alongside the session and never queried by field.
    # [MOMIN] This keeps reads single-row and avoids a join hot-path.
    references_json = models.JSONField(
        default=list,
        blank=True,
        help_text="Structured citations: file, optional line range, snippet",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True)
    # [MOMIN] checkout_path is persisted for reproducibility/auditing — given a
    # [MOMIN] session row, an operator can re-open the exact tree the agent saw.
    checkout_path = models.CharField(max_length=2048, blank=True)
    # [AI] Token aggregates from the OpenAI usage object (nullable when unknown).
    input_tokens = models.PositiveIntegerField(null=True, blank=True)
    output_tokens = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Session {self.pk}: {self.question[:60]}"


class Finding(models.Model):
    """Agent-authored note tied to a file (from save_finding tool)."""

    # [MOMIN] Findings are first-class rows (not embedded in the session JSON) so
    # [MOMIN] the agent can write them incrementally during a run, and so they
    # [MOMIN] survive across sessions for the same repository as durable knowledge.
    session = models.ForeignKey(
        ResearchSession,
        on_delete=models.CASCADE,
        related_name="findings",
    )
    file_path = models.CharField(max_length=1024, blank=True)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class ToolCallLog(models.Model):
    """Audit trail of tool invocations during a session."""

    # [MOMIN] Tool calls are logged at the boundary, not inside the runner, so the
    # [MOMIN] log accurately reflects what was *executed* (post-arg-parsing) rather
    # [MOMIN] than what the model proposed. Result excerpts are truncated upstream
    # [MOMIN] to keep individual rows bounded — see db_tools.log_tool_call.
    session = models.ForeignKey(
        ResearchSession,
        on_delete=models.CASCADE,
        related_name="tool_calls",
    )
    tool_name = models.CharField(max_length=128)
    arguments = models.JSONField(default=dict, blank=True)
    result_excerpt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

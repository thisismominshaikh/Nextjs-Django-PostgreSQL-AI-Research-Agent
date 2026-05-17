"""Django admin registration for the research app."""
from django.contrib import admin

from research.models import Finding, Repository, ResearchSession, ToolCallLog


class FindingInline(admin.TabularInline):
    model = Finding
    extra = 0
    readonly_fields = ("file_path", "note", "created_at")


class ToolCallLogInline(admin.TabularInline):
    model = ToolCallLog
    extra = 0
    readonly_fields = ("tool_name", "arguments", "result_excerpt", "created_at")


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("display_name", "identifier", "last_analyzed_at", "session_count")
    search_fields = ("identifier", "display_name")
    readonly_fields = ("last_analyzed_at",)

    def session_count(self, obj):
        return obj.sessions.count()
    session_count.short_description = "Sessions"


@admin.register(ResearchSession)
class ResearchSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "repository", "status", "question_preview", "input_tokens", "output_tokens", "created_at")
    list_filter = ("status", "repository")
    search_fields = ("question", "final_answer")
    readonly_fields = ("created_at", "updated_at", "input_tokens", "output_tokens")
    inlines = [FindingInline, ToolCallLogInline]

    def question_preview(self, obj):
        return obj.question[:80]
    question_preview.short_description = "Question"


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "file_path", "note_preview", "created_at")
    search_fields = ("file_path", "note")
    readonly_fields = ("created_at",)

    def note_preview(self, obj):
        return obj.note[:120]
    note_preview.short_description = "Note"


@admin.register(ToolCallLog)
class ToolCallLogAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "tool_name", "created_at")
    list_filter = ("tool_name",)
    readonly_fields = ("created_at",)

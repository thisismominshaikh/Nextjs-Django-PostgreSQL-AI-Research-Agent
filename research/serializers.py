# [AI] DRF serializers — thin projection layer over the ORM models.
from rest_framework import serializers

from research.models import Finding, Repository, ResearchSession, ToolCallLog


class FindingSerializer(serializers.ModelSerializer):
    # [AI] Surfaces a finding row as JSON.
    class Meta:
        model = Finding
        fields = ("id", "file_path", "note", "created_at")


class ToolCallLogSerializer(serializers.ModelSerializer):
    # [AI] Surfaces a tool-call audit row as JSON.
    class Meta:
        model = ToolCallLog
        fields = ("id", "tool_name", "arguments", "result_excerpt", "created_at")


class ResearchSessionSerializer(serializers.ModelSerializer):
    # [MOMIN] We expose `repository_identifier` as a denormalized read-only field so
    # [MOMIN] the frontend can render a session row without an extra Repository
    # [MOMIN] fetch. The numeric `repository` FK is kept too, for future linking.
    repository_identifier = serializers.CharField(source="repository.identifier", read_only=True)

    class Meta:
        model = ResearchSession
        # [MOMIN] Field list is enumerated explicitly (not "__all__") so adding
        # [MOMIN] internal columns later cannot accidentally leak through the API.
        fields = (
            "id",
            "repository",
            "repository_identifier",
            "question",
            "final_answer",
            "references_json",
            "status",
            "error_message",
            "checkout_path",
            "input_tokens",
            "output_tokens",
            "created_at",
            "updated_at",
        )
        # [MOMIN] Entire payload is read-only — sessions are *only* mutated by the
        # [MOMIN] agent runner, never by API clients.
        read_only_fields = fields


class ResearchSessionDetailSerializer(ResearchSessionSerializer):
    # [MOMIN] Detail view extends the list serializer with nested findings and tool
    # [MOMIN] calls. Kept on a separate class so list endpoints stay cheap and only
    # [MOMIN] the detail endpoint pays for the prefetched relations.
    findings = FindingSerializer(many=True, read_only=True)
    tool_calls = ToolCallLogSerializer(many=True, read_only=True)

    class Meta(ResearchSessionSerializer.Meta):
        fields = ResearchSessionSerializer.Meta.fields + ("findings", "tool_calls")


class StartResearchSessionSerializer(serializers.Serializer):
    # [MOMIN] This is a write-only validator (not a ModelSerializer) because the
    # [MOMIN] view orchestrates checkout + repo upsert + session create itself —
    # [MOMIN] we don't want serializer.save() to construct a half-initialized row.
    repo_url = serializers.CharField(
        help_text="Public Git HTTPS URL or absolute local path",
        max_length=2048,
    )
    question = serializers.CharField()


class RepositorySerializer(serializers.ModelSerializer):
    # [AI] Lightweight repo projection used by the past-sessions endpoint.
    class Meta:
        model = Repository
        fields = ("id", "identifier", "display_name", "last_analyzed_at")

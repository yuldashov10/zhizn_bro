from rest_framework import serializers

from apps.candidates.models import (
    Candidate,
    CandidateHardStopLog,
    CandidateStatusHistory,
)


class CandidateStatusHistorySerializer(serializers.ModelSerializer):
    """Сериализатор истории статусов кандидата."""

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = CandidateStatusHistory
        fields = [
            "id",
            "status",
            "status_display",
            "note",
            "started_at",
        ]
        read_only_fields = ["started_at"]


class CandidateStatusUpdateSerializer(serializers.Serializer):
    """Сериализатор для смены статуса кандидата."""

    status = serializers.ChoiceField(
        choices=CandidateStatusHistory.Status.choices,
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class CandidateHardStopLogSerializer(serializers.ModelSerializer):
    """Сериализатор лога срабатывания Hard Stop."""

    hard_stop_name = serializers.CharField(
        source="hard_stop.name",
        read_only=True,
    )

    class Meta:
        model = CandidateHardStopLog
        fields = [
            "id",
            "hard_stop",
            "hard_stop_name",
            "note",
            "triggered_at",
        ]
        read_only_fields = ["triggered_at"]


class CandidateSerializer(serializers.ModelSerializer):
    """Сериализатор кандидата (список)."""

    ai_attachment_type_display = serializers.CharField(
        source="get_ai_attachment_type_display",
        read_only=True,
    )

    class Meta:
        model = Candidate
        fields = [
            "id",
            "name",
            "age",
            "photo",
            "met_at",
            "is_active",
            "hard_stop_triggered",
            "ai_attachment_type",
            "ai_attachment_type_display",
            "created_at",
        ]
        read_only_fields = [
            "hard_stop_triggered",
            "ai_attachment_type",
            "created_at",
        ]


class CandidateDetailSerializer(CandidateSerializer):
    """Сериализатор кандидата (детали с историей статусов)."""

    status_history = CandidateStatusHistorySerializer(
        many=True,
        read_only=True,
    )
    hard_stop_logs = CandidateHardStopLogSerializer(
        many=True,
        read_only=True,
    )

    class Meta(CandidateSerializer.Meta):
        fields = CandidateSerializer.Meta.fields + [
            "status_history",
            "hard_stop_logs",
        ]


class CandidateScoreSerializer(serializers.Serializer):
    """Сериализатор итогового скора кандидата."""

    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField()
    score = serializers.IntegerField(allow_null=True)
    events_count = serializers.IntegerField()

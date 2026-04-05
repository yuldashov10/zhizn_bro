from rest_framework import serializers

from apps.reports.models import ReportLog


class ReportLogSerializer(serializers.ModelSerializer):
    """Сериализатор лога отчёта."""

    report_type_display = serializers.CharField(
        source="get_report_type_display",
        read_only=True,
    )
    trigger_display = serializers.CharField(
        source="get_trigger_display",
        read_only=True,
    )
    has_file = serializers.SerializerMethodField()

    class Meta:
        model = ReportLog
        fields = [
            "id",
            "candidate",
            "report_type",
            "report_type_display",
            "trigger",
            "trigger_display",
            "has_file",
            "file",
            "generated_at",
        ]
        read_only_fields = [
            "trigger",
            "generated_at",
        ]

    def get_has_file(self, obj: ReportLog) -> bool:
        return obj.has_file()


class ReportGenerateSerializer(serializers.Serializer):
    """Сериализатор запроса на генерацию отчёта."""

    candidate_id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
    report_type = serializers.ChoiceField(
        choices=ReportLog.ReportType.choices,
    )

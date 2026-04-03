from django.contrib import admin

from .models import ReportLog


@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    """Логи сгенерированных отчётов."""

    list_display = [
        "user",
        "candidate",
        "report_type",
        "trigger",
        "has_file",
        "generated_at",
    ]
    list_filter = [
        "report_type",
        "trigger",
    ]
    search_fields = [
        "user__telegram_id",
        "user__username",
        "candidate__name",
    ]
    readonly_fields = [
        "user",
        "candidate",
        "report_type",
        "trigger",
        "file",
        "generated_at",
    ]
    ordering = ["-generated_at"]

    @admin.display(description="Файл", boolean=True)
    def has_file(self, obj: ReportLog) -> bool:
        """Показывает прикреплён ли файл к отчёту."""
        return obj.has_file()

from django.contrib import admin

from .models import Candidate, CandidateHardStopLog, CandidateStatusHistory


class CandidateStatusHistoryInline(admin.TabularInline):
    """История статусов внутри карточки кандидата."""

    model = CandidateStatusHistory
    extra = 0
    readonly_fields = ["status", "started_at", "note"]
    can_delete = False
    ordering = ["-started_at"]
    fields = ["status", "started_at", "note"]


class CandidateHardStopLogInline(admin.TabularInline):
    """Логи срабатывания Hard Stop внутри карточки кандидата."""

    model = CandidateHardStopLog
    extra = 0
    readonly_fields = ["hard_stop", "triggered_at", "note"]
    can_delete = False
    ordering = ["-triggered_at"]
    fields = ["hard_stop", "triggered_at", "note"]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Кандидаты в партнёры."""

    inlines = [CandidateStatusHistoryInline, CandidateHardStopLogInline]

    list_display = [
        "name",
        "user",
        "age",
        "is_active",
        "hard_stop_triggered",
        "ai_attachment_type",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "hard_stop_triggered",
        "ai_attachment_type",
    ]
    search_fields = [
        "name",
        "user__telegram_id",
        "user__username",
    ]
    readonly_fields = [
        "created_at",
        "hard_stop_triggered",
        "ai_attachment_type",
    ]
    ordering = ["-created_at"]
    fieldsets = [
        (
            "Основное",
            {
                "fields": [
                    "user",
                    "name",
                    "age",
                    "photo",
                    "met_at",
                ],
            },
        ),
        (
            "Статус",
            {
                "fields": [
                    "is_active",
                    "hard_stop_triggered",
                    "ai_attachment_type",
                    "created_at",
                ],
            },
        ),
    ]


@admin.register(CandidateStatusHistory)
class CandidateStatusHistoryAdmin(admin.ModelAdmin):
    """История статусов кандидатов."""

    list_display = [
        "candidate",
        "status",
        "started_at",
        "note_preview",
    ]
    list_filter = ["status"]
    search_fields = [
        "candidate__name",
        "candidate__user__telegram_id",
    ]
    readonly_fields = ["started_at"]
    ordering = ["-started_at"]

    @admin.display(description="Причина")
    def note_preview(self, obj: CandidateStatusHistory) -> str:
        """Показывает первые 60 символов причины смены статуса."""
        if not obj.note:
            return "—"
        return obj.note[:60] + "..." if len(obj.note) > 60 else obj.note


@admin.register(CandidateHardStopLog)
class CandidateHardStopLogAdmin(admin.ModelAdmin):
    """Логи срабатывания Hard Stop."""

    list_display = [
        "candidate",
        "hard_stop",
        "triggered_at",
        "note_preview",
    ]
    list_filter = ["hard_stop"]
    search_fields = [
        "candidate__name",
        "candidate__user__telegram_id",
        "hard_stop__name",
    ]
    readonly_fields = ["triggered_at"]
    ordering = ["-triggered_at"]

    @admin.display(description="Описание события")
    def note_preview(self, obj: CandidateHardStopLog) -> str:
        """Показывает первые 60 символов описания события-триггера."""
        if not obj.note:
            return "—"
        return obj.note[:60] + "..." if len(obj.note) > 60 else obj.note

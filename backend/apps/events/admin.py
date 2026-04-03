from django.contrib import admin

from .models import AIProviderLog, Event, EventCriterionScore


class EventCriterionScoreInline(admin.TabularInline):
    """Оценки по критериям внутри карточки события."""

    model = EventCriterionScore
    extra = 0
    readonly_fields = ["ai_score", "final_score"]
    fields = [
        "criterion",
        "ai_score",
        "user_score",
        "is_confirmed",
        "final_score",
    ]

    @admin.display(description="Итоговый балл")
    def final_score(self, obj: EventCriterionScore) -> int:
        """Показывает итоговый балл с учётом корректировки пользователя."""
        return obj.final_score


class AIProviderLogInline(admin.TabularInline):
    """Логи AI провайдера внутри карточки события."""

    model = AIProviderLog
    extra = 0
    can_delete = False
    readonly_fields = [
        "provider",
        "tokens_used",
        "created_at",
        "prompt_preview",
    ]
    fields = [
        "provider",
        "tokens_used",
        "created_at",
        "prompt_preview",
    ]

    @admin.display(description="Промпт")
    def prompt_preview(self, obj: AIProviderLog) -> str:
        """Показывает первые 60 символов промпта."""
        return obj.prompt[:60] + "..." if len(obj.prompt) > 60 else obj.prompt


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """События — зафиксированные факты поведения кандидата."""

    inlines = [EventCriterionScoreInline, AIProviderLogInline]

    list_display = [
        "candidate",
        "raw_text_preview",
        "is_hard_stop",
        "has_bias_warning",
        "scores_count",
        "created_at",
    ]
    list_filter = [
        "is_hard_stop",
        "candidate__user",
    ]
    search_fields = [
        "raw_text",
        "ai_interpretation",
        "candidate__name",
        "candidate__user__telegram_id",
    ]
    readonly_fields = [
        "ai_interpretation",
        "bias_warning",
        "is_hard_stop",
        "created_at",
    ]
    ordering = ["-created_at"]
    fieldsets = [
        (
            "Событие",
            {
                "fields": [
                    "candidate",
                    "raw_text",
                    "created_at",
                ],
            },
        ),
        (
            "Анализ ИИ",
            {
                "fields": [
                    "ai_interpretation",
                    "bias_warning",
                    "is_hard_stop",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Текст события")
    def raw_text_preview(self, obj: Event) -> str:
        """Показывает первые 60 символов текста события."""
        return (
            obj.raw_text[:60] + "..."
            if len(obj.raw_text) > 60
            else obj.raw_text
        )

    @admin.display(description="Искажение", boolean=True)
    def has_bias_warning(self, obj: Event) -> bool:
        """Показывает есть ли предупреждение о когнитивном искажении."""
        return obj.has_bias_warning()

    @admin.display(description="Оценок")
    def scores_count(self, obj: Event) -> int:
        """Показывает количество оценок по критериям."""
        return obj.scores.count()


@admin.register(EventCriterionScore)
class EventCriterionScoreAdmin(admin.ModelAdmin):
    """Оценки событий по критериям."""

    list_display = [
        "event",
        "criterion",
        "ai_score",
        "user_score",
        "final_score",
        "is_confirmed",
    ]
    list_filter = [
        "is_confirmed",
        "criterion",
    ]
    search_fields = [
        "event__raw_text",
        "event__candidate__name",
    ]
    readonly_fields = ["ai_score"]
    ordering = ["event", "criterion"]

    @admin.display(description="Итоговый балл")
    def final_score(self, obj: EventCriterionScore) -> int:
        """Показывает итоговый балл с учётом корректировки пользователя."""
        return obj.final_score


@admin.register(AIProviderLog)
class AIProviderLogAdmin(admin.ModelAdmin):
    """Логи запросов к AI провайдеру."""

    list_display = [
        "provider",
        "tokens_used",
        "event",
        "created_at",
    ]
    list_filter = ["provider"]
    search_fields = [
        "event__candidate__name",
        "event__raw_text",
    ]
    readonly_fields = [
        "provider",
        "prompt",
        "response",
        "tokens_used",
        "created_at",
    ]
    ordering = ["-created_at"]

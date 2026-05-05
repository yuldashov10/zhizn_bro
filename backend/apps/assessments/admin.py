from django.contrib import admin

from .models import AttachmentTest, Question, UserAnswer, UserTestSession


class QuestionInline(admin.TabularInline):
    """Вопросы внутри карточки теста."""

    model = Question
    extra = 0
    fields = ["order", "text", "dimension", "weight"]
    ordering = ["order"]


class UserAnswerInline(admin.TabularInline):
    """Ответы пользователя внутри сессии теста."""

    model = UserAnswer
    extra = 0
    readonly_fields = ["question", "answer"]
    can_delete = False
    fields = ["question", "answer"]


@admin.register(AttachmentTest)
class AttachmentTestAdmin(admin.ModelAdmin):
    """Тесты привязанности с вопросами."""

    inlines = [QuestionInline]

    list_display = [
        "name",
        "questions_count",
        "is_validated",
        "is_active",
    ]
    list_filter = [
        "is_validated",
        "is_active",
    ]
    search_fields = ["name", "description"]
    ordering = ["-is_validated", "name"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Вопросы тестов."""

    list_display = [
        "test",
        "order",
        "dimension",
        "weight",
        "text_preview",
    ]
    list_filter = [
        "test",
        "dimension",
    ]
    search_fields = ["text"]
    ordering = ["test", "order"]

    @admin.display(description="Текст вопроса")
    def text_preview(self, obj: Question) -> str:
        """Показывает первые 60 символов текста вопроса."""
        return obj.text[:60] + "..." if len(obj.text) > 60 else obj.text


@admin.register(UserTestSession)
class UserTestSessionAdmin(admin.ModelAdmin):
    """Сессии прохождения тестов."""

    inlines = [UserAnswerInline]

    list_display = [
        "user",
        "test",
        "result_type",
        "is_completed",
        "completed_at",
    ]
    list_filter = [
        "test",
        "result_type",
    ]
    search_fields = [
        "user__telegram_id",
        "user__username",
    ]
    readonly_fields = ["completed_at"]
    ordering = ["-completed_at"]

    @admin.display(description="Завершена", boolean=True)
    def is_completed(self, obj: UserTestSession) -> bool:
        """Показывает завершена ли сессия."""
        return obj.is_completed()

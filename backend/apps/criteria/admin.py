from django.contrib import admin

from apps.criteria.models import (
    Criterion,
    HardStop,
    HardStopSuggestion,
    UserCriterionSettings,
    UserHardStopSettings,
)
from core.mixins import SystemObjectReadonlyMixin
from core.utils import truncate


@admin.register(HardStop)
class HardStopAdmin(SystemObjectReadonlyMixin, admin.ModelAdmin):
    """Hard Stops — абсолютные фильтры."""

    list_display = [
        "name",
        "is_default",
        "is_active",
        "user",
    ]
    list_select_related = ["user"]
    list_filter = [
        "is_default",
        "is_active",
    ]
    search_fields = [
        "name",
        "description",
        "user__telegram_id",
        "user__username",
    ]
    ordering = ["-is_default", "name"]
    readonly_fields = ["user"]


@admin.register(Criterion)
class CriterionAdmin(SystemObjectReadonlyMixin, admin.ModelAdmin):
    """Критерии оценки кандидата."""

    list_display = [
        "name",
        "weight_display",
        "is_default",
        "is_active",
        "user",
    ]
    list_select_related = ["user"]
    list_filter = [
        "is_default",
        "is_active",
    ]
    search_fields = [
        "name",
        "description",
        "user__telegram_id",
        "user__username",
    ]
    ordering = ["-is_default", "-weight"]
    readonly_fields = ["user"]

    @admin.display(description="Вес")
    def weight_display(self, obj: Criterion) -> str:
        """Отображает вес критерия в процентах."""
        return f"{obj.weight * 100:.0f}%"


@admin.register(HardStopSuggestion)
class HardStopSuggestionAdmin(admin.ModelAdmin):
    """Предложения пользователей по новым Hard Stops."""

    list_display = [
        "user",
        "text_preview",
        "status",
        "created_at",
    ]
    list_select_related = ["user"]
    list_filter = ["status"]
    search_fields = [
        "user__telegram_id",
        "user__username",
        "text",
    ]
    readonly_fields = ["user", "text", "created_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    actions = ["approve_suggestions", "reject_suggestions"]

    @admin.display(description="Предложение")
    def text_preview(self, obj: HardStopSuggestion) -> str:
        return truncate(obj.text)

    @admin.action(description="Одобрить выбранные")
    def approve_suggestions(self, request, queryset):
        queryset.update(status=HardStopSuggestion.Status.APPROVED)

    @admin.action(description="Отклонить выбранные")
    def reject_suggestions(self, request, queryset):
        queryset.update(status=HardStopSuggestion.Status.REJECTED)


@admin.register(UserHardStopSettings)
class UserHardStopSettingsAdmin(admin.ModelAdmin):
    """Настройки Hard Stops пользователей."""

    list_display = ["user", "hard_stop", "is_active"]
    list_select_related = ["user", "hard_stop"]
    list_filter = ["is_active"]
    search_fields = [
        "user__telegram_id",
        "user__username",
        "hard_stop__name",
    ]
    readonly_fields = ["user", "hard_stop"]


@admin.register(UserCriterionSettings)
class UserCriterionSettingsAdmin(admin.ModelAdmin):
    """Настройки критериев пользователей."""

    list_display = ["user", "criterion", "is_active"]
    list_select_related = ["user", "criterion"]
    list_filter = ["is_active"]
    search_fields = [
        "user__telegram_id",
        "user__username",
        "criterion__name",
    ]
    readonly_fields = ["user", "criterion"]

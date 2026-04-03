from django.contrib import admin

from .models import Criterion, HardStop


@admin.register(HardStop)
class HardStopAdmin(admin.ModelAdmin):
    """Hard Stops — абсолютные фильтры."""

    list_display = [
        "name",
        "is_default",
        "is_active",
        "user",
    ]
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

    def get_readonly_fields(self, request, obj=None):
        """
        Системные Hard Stops нельзя редактировать.
        Поле user доступно только при создании пользовательского.
        """
        if obj and obj.is_default:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    """Критерии оценки кандидата."""

    list_display = [
        "name",
        "weight_display",
        "is_default",
        "is_active",
        "user",
    ]
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

    def get_readonly_fields(self, request, obj=None):
        """Системные критерии нельзя редактировать."""
        if obj and obj.is_default:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    @admin.display(description="Вес")
    def weight_display(self, obj: Criterion) -> str:
        """Отображает вес критерия в процентах."""
        return f"{obj.weight * 100:.0f}%"

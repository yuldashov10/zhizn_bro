from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile, UserTokenLimit


class UserProfileInline(admin.StackedInline):
    """Профиль пользователя внутри карточки пользователя."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"
    readonly_fields = ["updated_at"]
    fields = [
        "attachment_type",
        "attachment_source",
        "correction_coefficient",
        "test_session",
        "updated_at",
    ]


class UserTokenLimitInline(admin.StackedInline):
    """Лимиты токенов внутри карточки пользователя."""

    model = UserTokenLimit
    can_delete = False
    verbose_name_plural = "Лимиты токенов"
    readonly_fields = ["used_today", "used_this_month", "reset_at"]
    fields = [
        "tier",
        "daily_limit",
        "monthly_limit",
        "used_today",
        "used_this_month",
        "reset_at",
    ]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Кастомный админ для пользователя.
    Переопределяет стандартный UserAdmin под нашу модель без email/first_name.
    """

    inlines = [UserProfileInline, UserTokenLimitInline]

    list_display = [
        "telegram_id",
        "username",
        "language",
        "is_active",
        "is_staff",
        "date_joined",
    ]
    list_filter = [
        "is_active",
        "is_staff",
        "language",
    ]
    search_fields = [
        "telegram_id",
        "username",
    ]
    ordering = ["-date_joined"]
    readonly_fields = ["date_joined", "last_login"]

    # Переопределяем fieldsets — убираем email, first_name, last_name
    fieldsets = [
        (
            "Основное",
            {
                "fields": ["telegram_id", "username", "language"],
            },
        ),
        (
            "Права доступа",
            {
                "fields": [
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Даты",
            {
                "fields": ["date_joined", "last_login"],
                "classes": ["collapse"],
            },
        ),
    ]

    # Форма создания пользователя
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "telegram_id",
                    "username",
                    "language",
                    "password1",
                    "password2",
                ],
            },
        ),
    ]

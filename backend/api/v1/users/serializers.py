from rest_framework import serializers

from apps.users.models import User, UserProfile, UserTokenLimit


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя."""

    attachment_type_display = serializers.CharField(
        source="get_attachment_type_display",
        read_only=True,
    )
    attachment_source_display = serializers.CharField(
        source="get_attachment_source_display",
        read_only=True,
    )

    class Meta:
        model = UserProfile
        fields = [
            "attachment_type",
            "attachment_type_display",
            "attachment_source",
            "attachment_source_display",
            "correction_coefficient",
            "updated_at",
        ]
        read_only_fields = [
            "attachment_source",
            "correction_coefficient",
            "updated_at",
        ]


class UserTokenLimitSerializer(serializers.ModelSerializer):
    """Сериализатор лимитов токенов пользователя."""

    is_daily_limit_exceeded = serializers.SerializerMethodField()
    is_monthly_limit_exceeded = serializers.SerializerMethodField()
    tier_display = serializers.CharField(
        source="get_tier_display",
        read_only=True,
    )

    class Meta:
        model = UserTokenLimit
        fields = [
            "tier",
            "tier_display",
            "daily_limit",
            "monthly_limit",
            "used_today",
            "used_this_month",
            "is_daily_limit_exceeded",
            "is_monthly_limit_exceeded",
            "reset_at",
        ]
        read_only_fields = [
            "used_today",
            "used_this_month",
            "reset_at",
        ]

    def get_is_daily_limit_exceeded(self, obj: UserTokenLimit) -> bool:
        return obj.is_daily_limit_exceeded()

    def get_is_monthly_limit_exceeded(self, obj: UserTokenLimit) -> bool:
        return obj.is_monthly_limit_exceeded()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя с профилем и лимитами."""

    profile = UserProfileSerializer(read_only=True)
    token_limit = UserTokenLimitSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "telegram_id",
            "username",
            "language",
            "date_joined",
            "profile",
            "token_limit",
        ]
        read_only_fields = [
            "id",
            "telegram_id",
            "date_joined",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления пользователя.
    Пользователь может менять только язык интерфейса.
    """

    class Meta:
        model = User
        fields = ["language"]


class TelegramAuthSerializer(serializers.Serializer):
    """
    Сериализатор аутентификации через Telegram.
    Принимает telegram_id и возвращает токен.
    """

    telegram_id = serializers.IntegerField()
    username = serializers.CharField(
        max_length=64,
        required=False,
        allow_null=True,
    )

    def validate_telegram_id(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError(
                "Telegram ID должен быть положительным числом."
            )
        return value

from rest_framework import serializers

from apps.criteria.models import Criterion, HardStop, HardStopSuggestion


class HardStopSuggestionSerializer(serializers.ModelSerializer):
    """Сериализатор предложения Hard Stop."""

    class Meta:
        model = HardStopSuggestion
        fields = ["id", "text", "status", "created_at"]
        read_only_fields = ["status", "created_at"]

    def validate_text(self, value: str) -> str:
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Предложение должно содержать минимум 10 символов."
            )
        return value.strip()


class HardStopSerializer(serializers.ModelSerializer):
    """Сериализатор Hard Stop."""

    is_system = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = HardStop
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_active",
            "is_system",
        ]
        read_only_fields = ["is_default", "name", "description"]

    def get_is_system(self, obj: HardStop) -> bool:
        return obj.is_system()

    def get_is_active(self, obj: HardStop) -> bool:
        """Активен ли Hard Stop для текущего пользователя."""
        user_settings = self.context.get("user_settings", {})
        return user_settings.get(obj.pk, True)

    def validate(self, attrs: dict) -> dict:
        """Запрещает изменение системных Hard Stops."""
        if self.instance and self.instance.is_default:
            allowed = {"is_active"}
            extra = set(attrs.keys()) - allowed
            if extra:
                raise serializers.ValidationError(
                    "Системный Hard Stop можно "
                    "только активировать/деактивировать."
                )
        return attrs


class CriterionSerializer(serializers.ModelSerializer):
    """Сериализатор критерия оценки."""

    is_system = serializers.SerializerMethodField()
    weight_display = serializers.SerializerMethodField()
    effective_weight = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Criterion
        fields = [
            "id",
            "name",
            "description",
            "weight",
            "weight_display",
            "effective_weight",
            "is_default",
            "is_active",
            "is_system",
        ]
        read_only_fields = ["is_default", "name", "description", "weight"]

    def get_is_system(self, obj: Criterion) -> bool:
        return obj.is_system()

    def get_weight_display(self, obj: Criterion) -> str:
        return f"{obj.weight * 100:.0f}%"

    def get_is_active(self, obj: Criterion) -> bool:
        """Активен ли критерий для текущего пользователя."""
        user_settings = self.context.get("user_settings", {})
        return user_settings.get(obj.pk, True)

    def get_effective_weight(self, obj: Criterion) -> str:
        """Эффективный вес с учётом отключённых критериев."""
        user_settings = self.context.get("user_settings", {})
        weights = self.context.get("weights", {})
        is_active = user_settings.get(obj.pk, True)
        if not is_active:
            return "выкл"
        w = weights.get(obj.name, 0)
        return f"{w * 100:.1f}%"

    def validate(self, attrs: dict) -> dict:
        """Запрещает изменение системных критериев."""
        if self.instance and self.instance.is_default:
            allowed = {"is_active"}
            extra = set(attrs.keys()) - allowed
            if extra:
                raise serializers.ValidationError(
                    "Системный критерий можно "
                    "только активировать/деактивировать."
                )
        return attrs

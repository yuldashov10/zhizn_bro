from rest_framework import serializers

from apps.criteria.models import Criterion, HardStop


class HardStopSerializer(serializers.ModelSerializer):
    """Сериализатор Hard Stop."""

    is_system = serializers.SerializerMethodField()

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
        read_only_fields = ["is_default"]

    def get_is_system(self, obj: HardStop) -> bool:
        return obj.is_system()

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

    class Meta:
        model = Criterion
        fields = [
            "id",
            "name",
            "description",
            "weight",
            "weight_display",
            "is_default",
            "is_active",
            "is_system",
        ]
        read_only_fields = ["is_default"]

    def get_is_system(self, obj: Criterion) -> bool:
        return obj.is_system()

    def get_weight_display(self, obj: Criterion) -> str:
        return f"{obj.weight * 100:.0f}%"

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

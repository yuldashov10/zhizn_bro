from rest_framework import serializers

from apps.events.models import AIProviderLog, Event, EventCriterionScore


class EventCriterionScoreSerializer(serializers.ModelSerializer):
    """Сериализатор оценки события по критерию."""

    criterion_name = serializers.CharField(
        source="criterion.name",
        read_only=True,
    )
    final_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = EventCriterionScore
        fields = [
            "id",
            "criterion",
            "criterion_name",
            "ai_score",
            "user_score",
            "final_score",
            "is_confirmed",
        ]
        read_only_fields = ["ai_score"]


class EventCriterionScoreConfirmSerializer(serializers.ModelSerializer):
    """
    Сериализатор подтверждения оценки ИИ пользователем.
    Пользователь может скорректировать балл и подтвердить.
    """

    class Meta:
        model = EventCriterionScore
        fields = [
            "user_score",
            "is_confirmed",
        ]

    def validate_user_score(self, value: int | None) -> int | None:
        if value is not None and not -2 <= value <= 2:
            raise serializers.ValidationError(
                "Балл должен быть в диапазоне от -2 до +2."
            )
        return value


class EventSerializer(serializers.ModelSerializer):
    """Сериализатор события (список)."""

    scores_count = serializers.SerializerMethodField()
    has_bias_warning = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "candidate",
            "raw_text",
            "is_hard_stop",
            "has_bias_warning",
            "scores_count",
            "created_at",
        ]
        read_only_fields = [
            "is_hard_stop",
            "created_at",
        ]

    def get_scores_count(self, obj: Event) -> int:
        return obj.scores.count()

    def get_has_bias_warning(self, obj: Event) -> bool:
        return obj.has_bias_warning()


class EventDetailSerializer(EventSerializer):
    """Сериализатор события (детали с оценками)."""

    scores = EventCriterionScoreSerializer(many=True, read_only=True)

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + [
            "ai_interpretation",
            "bias_warning",
            "scores",
        ]


class EventCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания события.
    Принимает только raw_text и candidate — остальное заполняет ИИ.
    """

    class Meta:
        model = Event
        fields = [
            "candidate",
            "raw_text",
        ]

    def validate_raw_text(self, value: str) -> str:
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Описание события должно содержать не менее 10 символов."
            )
        return value.strip()


class AIProviderLogSerializer(serializers.ModelSerializer):
    """Сериализатор лога AI провайдера."""

    provider_display = serializers.CharField(
        source="get_provider_display",
        read_only=True,
    )

    class Meta:
        model = AIProviderLog
        fields = [
            "id",
            "provider",
            "provider_display",
            "tokens_used",
            "created_at",
        ]

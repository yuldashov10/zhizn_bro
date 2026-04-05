from rest_framework import serializers

from apps.assessments.models import (
    AttachmentTest,
    Question,
    UserAnswer,
    UserTestSession,
)


class QuestionSerializer(serializers.ModelSerializer):
    """Сериализатор вопроса теста."""

    dimension_display = serializers.CharField(
        source="get_dimension_display",
        read_only=True,
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "dimension",
            "dimension_display",
            "order",
        ]


class AttachmentTestSerializer(serializers.ModelSerializer):
    """Сериализатор теста привязанности (список)."""

    class Meta:
        model = AttachmentTest
        fields = [
            "id",
            "name",
            "description",
            "questions_count",
            "is_validated",
        ]


class AttachmentTestDetailSerializer(serializers.ModelSerializer):
    """Сериализатор теста привязанности (детали с вопросами)."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = AttachmentTest
        fields = [
            "id",
            "name",
            "description",
            "questions_count",
            "is_validated",
            "questions",
        ]


class UserAnswerSerializer(serializers.ModelSerializer):
    """Сериализатор ответа на вопрос теста."""

    class Meta:
        model = UserAnswer
        fields = [
            "question",
            "answer",
        ]

    def validate_answer(self, value: int) -> int:
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Ответ должен быть в диапазоне от 1 до 5."
            )
        return value


class UserTestSessionSerializer(serializers.ModelSerializer):
    """Сериализатор сессии теста."""

    test = AttachmentTestSerializer(read_only=True)
    result_type_display = serializers.CharField(
        source="get_result_type_display",
        read_only=True,
    )
    is_completed = serializers.SerializerMethodField()
    answers_count = serializers.SerializerMethodField()

    class Meta:
        model = UserTestSession
        fields = [
            "id",
            "test",
            "result_type",
            "result_type_display",
            "is_completed",
            "answers_count",
            "completed_at",
        ]
        read_only_fields = [
            "result_type",
            "completed_at",
        ]

    def get_is_completed(self, obj: UserTestSession) -> bool:
        return obj.is_completed()

    def get_answers_count(self, obj: UserTestSession) -> int:
        return obj.answers.count()

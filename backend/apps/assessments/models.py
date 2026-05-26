from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.users.models import User
from core.choices import AttachmentType


class AttachmentTest(models.Model):
    """
    Тест для определения типа привязанности.
    Может быть академически валидированным (ECR-R, RSQ, ASQ) или кастомным.
    """

    name = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Название теста",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание методологии",
    )
    questions_count = models.IntegerField(
        default=0,
        verbose_name="Количество вопросов",
    )
    is_validated = models.BooleanField(
        default=False,
        verbose_name="Академически валидирован",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Доступен пользователям",
    )

    class Meta:
        verbose_name = "Тест привязанности"
        verbose_name_plural = "Тесты привязанности"
        ordering = ("-is_validated", "name")

    def __str__(self) -> str:
        return self.name


class Question(models.Model):
    """
    Вопрос теста привязанности.
    Относится к одному из двух измерений: тревожность или избегание.
    """

    class Dimension(models.TextChoices):
        ANXIETY = "anxiety", "Тревожность"
        AVOIDANCE = "avoidance", "Избегание"

    test = models.ForeignKey(
        AttachmentTest,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Тест",
    )
    text = models.TextField(
        verbose_name="Текст вопроса",
    )
    dimension = models.CharField(
        max_length=20,
        choices=Dimension.choices,
        verbose_name="Измерение",
    )
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0)],
        verbose_name="Вес вопроса",
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Порядок отображения",
    )

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ("test", "order")

    def __str__(self) -> str:
        return f"[{self.test}] #{self.order} {self.text[:50]}"


class UserTestSession(models.Model):
    """
    Сессия прохождения теста пользователем.
    Хранит итоговый тип привязанности после завершения теста.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="test_sessions",
        verbose_name="Пользователь",
    )
    test = models.ForeignKey(
        AttachmentTest,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Тест",
    )
    result_type = models.CharField(
        max_length=20,
        choices=AttachmentType.choices,
        blank=True,
        null=True,
        verbose_name="Результат теста",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата завершения",
    )

    class Meta:
        verbose_name = "Сессия теста"
        verbose_name_plural = "Сессии тестов"
        ordering = ("-completed_at",)

    def __str__(self) -> str:
        return f"{self.user} → {self.test} [{self.result_type}]"

    def is_completed(self) -> bool:
        """Проверяет завершена ли сессия."""
        return self.completed_at is not None


class UserAnswer(models.Model):
    """
    Ответ пользователя на вопрос теста.
    Шкала Лайкерта от 1 до 5.
    """

    session = models.ForeignKey(
        UserTestSession,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Сессия",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Вопрос",
    )
    answer = models.SmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Ответ (1–5)",
    )

    class Meta:
        verbose_name = "Ответ на вопрос"
        verbose_name_plural = "Ответы на вопросы"
        unique_together = [["session", "question"]]

    def __str__(self) -> str:
        return f"{self.session} | {self.question} → {self.answer}"

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.candidates.models import Candidate
from apps.criteria.models import Criterion


class Event(models.Model):
    """
    Зафиксированное событие — конкретный факт поведения кандидата.
    ИИ анализирует свободный текст и предлагает категорию и балл.
    """

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Кандидат",
    )
    raw_text = models.TextField(
        verbose_name="Текст события (оригинал пользователя)",
    )
    ai_interpretation = models.TextField(
        blank=True,
        verbose_name="Интерпретация ИИ",
    )
    is_hard_stop = models.BooleanField(
        default=False,
        verbose_name="Триггернуло Hard Stop",
    )
    bias_warning = models.TextField(
        blank=True,
        verbose_name="Предупреждение о когнитивном искажении",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время события",
    )

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.candidate} | {self.raw_text[:60]}"

    def has_bias_warning(self) -> bool:
        """Проверяет есть ли предупреждение о когнитивном искажении."""
        return bool(self.bias_warning)


class EventCriterionScore(models.Model):
    """
    Оценка события по конкретному критерию.
    Одно событие может затрагивать несколько критериев одновременно.
    Хранит как оценку ИИ так и скорректированную оценку пользователя.
    """

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name="Событие",
    )
    criterion = models.ForeignKey(
        Criterion,
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name="Критерий",
    )
    ai_score = models.SmallIntegerField(
        validators=[MinValueValidator(-2), MaxValueValidator(2)],
        verbose_name="Балл ИИ (-2..+2)",
    )
    user_score = models.SmallIntegerField(
        validators=[MinValueValidator(-2), MaxValueValidator(2)],
        null=True,
        blank=True,
        verbose_name="Балл пользователя (-2..+2)",
    )
    is_confirmed = models.BooleanField(
        default=False,
        verbose_name="Пользователь подтвердил оценку",
    )

    class Meta:
        verbose_name = "Оценка события"
        verbose_name_plural = "Оценки событий"
        unique_together = [["event", "criterion"]]
        ordering = ["event", "criterion"]

    def __str__(self) -> str:
        return f"{self.event} | {self.criterion} → {self.final_score}"

    @property
    def final_score(self) -> int:
        """
        Возвращает итоговый балл.
        Если пользователь скорректировал — его оценка, иначе оценка ИИ.
        """
        return (
            self.user_score if self.user_score is not None else self.ai_score
        )


class AIProviderLog(models.Model):
    """
    Лог запросов к AI провайдеру.
    Используется для отладки и мониторинга расхода токенов.
    """

    class Provider(models.TextChoices):
        CLAUDE = "claude", "Claude"
        GEMINI = "gemini", "Gemini"
        OPENAI = "openai", "OpenAI"

    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_logs",
        verbose_name="Событие",
    )
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        verbose_name="Провайдер",
    )
    prompt = models.TextField(
        verbose_name="Отправленный промпт",
    )
    response = models.TextField(
        verbose_name="Ответ провайдера",
    )
    tokens_used = models.IntegerField(
        default=0,
        verbose_name="Использовано токенов",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время запроса",
    )

    class Meta:
        verbose_name = "Лог AI провайдера"
        verbose_name_plural = "Логи AI провайдера"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"[{self.provider}] "
            f"{self.created_at:%d.%m.%Y %H:%M} "
            f"| {self.tokens_used} токенов"
        )

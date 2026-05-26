from django.db import models

from apps.criteria.models import HardStop
from apps.users.models import User
from core.choices import AttachmentType


class Candidate(models.Model):
    """
    Кандидат в партнёры — девушка которую оценивает пользователь.
    Тип привязанности определяется ИИ автоматически на основе событий.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="candidates",
        verbose_name="Пользователь",
    )
    name = models.CharField(
        max_length=128,
        verbose_name="Имя / псевдоним",
    )
    age = models.SmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Возраст",
    )
    photo = models.ImageField(
        upload_to="candidates/photos/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Фото",
    )
    telegram_photo_id = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="Telegram file_id фото",
    )
    met_at = models.CharField(
        max_length=128,
        blank=True,
        verbose_name="Место / обстоятельства знакомства",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активный кандидат",
    )
    hard_stop_triggered = models.BooleanField(
        default=False,
        verbose_name="Сработал Hard Stop",
    )
    ai_attachment_type = models.CharField(
        max_length=20,
        choices=AttachmentType.choices,
        blank=True,
        null=True,
        verbose_name="Тип привязанности (определён ИИ)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления",
    )

    class Meta:
        verbose_name = "Кандидат"
        verbose_name_plural = "Кандидаты"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} [{self.user}]"

    def archive(self) -> None:
        """Переводит кандидата в архив."""
        self.is_active = False
        self.save(update_fields=["is_active"])


class CandidateStatusHistory(models.Model):
    """
    История смены статусов кандидата.
    Позволяет отслеживать динамику и паттерны нестабильности.
    """

    class Status(models.TextChoices):
        MEETING = "meeting", "Знакомство"
        DATING = "dating", "Встречаемся"
        SERIOUS = "serious", "Серьёзно"
        PAUSE = "pause", "Пауза"
        ENDED = "ended", "Завершено"

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Кандидат",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        verbose_name="Статус",
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата установки статуса",
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата завершения статуса",
    )
    note = models.TextField(
        blank=True,
        verbose_name="Причина смены статуса",
    )

    class Meta:
        verbose_name = "История статусов"
        verbose_name_plural = "История статусов"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.candidate} → {self.get_status_display()}"


class CandidateHardStopLog(models.Model):
    """
    Лог срабатывания Hard Stop для кандидата.
    Фиксирует какой именно фильтр сработал и когда.
    """

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="hard_stop_logs",
        verbose_name="Кандидат",
    )
    hard_stop = models.ForeignKey(
        HardStop,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Hard Stop",
    )
    triggered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата срабатывания",
    )
    note = models.TextField(
        blank=True,
        verbose_name="Описание события-триггера",
    )

    class Meta:
        verbose_name = "Лог Hard Stop"
        verbose_name_plural = "Логи Hard Stop"
        ordering = ["-triggered_at"]

    def __str__(self) -> str:
        return (
            f"{self.candidate} "
            f"| {self.hard_stop} "
            f"[{self.triggered_at:%d.%m.%Y}]"
        )

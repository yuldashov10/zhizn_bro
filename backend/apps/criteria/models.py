from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.users.models import User


class HardStop(models.Model):
    """
    Абсолютный фильтр — критерий немедленного прекращения оценки.
    Системные HardStop видны всем пользователям (user=None).
    Пользовательские привязаны к конкретному пользователю.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hard_stops",
        verbose_name="Пользователь",
    )
    name = models.CharField(
        max_length=128,
        verbose_name="Название",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание и логика",
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Системный (предустановленный)",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    class Meta:
        verbose_name = "Hard Stop"
        verbose_name_plural = "Hard Stops"
        ordering = ["-is_default", "name"]

    def __str__(self) -> str:
        prefix = "[Системный]" if self.is_default else f"[{self.user}]"
        return f"{prefix} {self.name}"

    def is_system(self) -> bool:
        """Проверяет является ли Hard Stop системным."""
        return self.user is None and self.is_default


class Criterion(models.Model):
    """
    Критерий оценки кандидата.
    Системные критерии (user=None) доступны всем пользователям.
    Сумма весов активных критериев должна быть равна 1.0.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="criteria",
        verbose_name="Пользователь",
    )
    name = models.CharField(
        max_length=64,
        verbose_name="Название",
    )
    weight = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Вес критерия (0.0–1.0)",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Что измеряется",
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Системный (предустановленный)",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    class Meta:
        verbose_name = "Критерий оценки"
        verbose_name_plural = "Критерии оценки"
        ordering = ["-is_default", "-weight"]

    def __str__(self) -> str:
        prefix = "[Системный]" if self.is_default else f"[{self.user}]"
        return f"{prefix} {self.name} ({self.weight * 100:.0f}%)"

    def is_system(self) -> bool:
        """Проверяет является ли критерий системным."""
        return self.user is None and self.is_default


class HardStopSuggestion(models.Model):
    """
    Предложение пользователя добавить новый системный Hard Stop.
    Рассматривается администратором вручную.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрено"
        REJECTED = "rejected", "Отклонено"

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="hard_stop_suggestions",
        verbose_name="Пользователь",
    )
    text = models.TextField(
        verbose_name="Предложение",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )
    admin_note = models.TextField(
        blank=True,
        verbose_name="Комментарий администратора",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата предложения",
    )

    class Meta:
        verbose_name = "Предложение Hard Stop"
        verbose_name_plural = "Предложения Hard Stop"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"@{self.user.username or self.user.telegram_id} "
            f"— {self.text[:50]}"
        )


class UserHardStopSettings(models.Model):
    """
    Пользовательские настройки Hard Stop.
    Хранит включён/выключен системный Hard Stop для конкретного пользователя.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="hard_stop_settings",
        verbose_name="Пользователь",
    )
    hard_stop = models.ForeignKey(
        HardStop,
        on_delete=models.CASCADE,
        related_name="user_settings",
        verbose_name="Hard Stop",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    class Meta:
        verbose_name = "Настройки Hard Stop"
        verbose_name_plural = "Настройки Hard Stops"
        unique_together = [["user", "hard_stop"]]

    def __str__(self) -> str:
        status = "вкл" if self.is_active else "выкл"
        return f"{self.user} — {self.hard_stop.name} [{status}]"


class UserCriterionSettings(models.Model):
    """
    Пользовательские настройки критерия.
    Хранит включён/выключен критерий для конкретного пользователя.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="criterion_settings",
        verbose_name="Пользователь",
    )
    criterion = models.ForeignKey(
        Criterion,
        on_delete=models.CASCADE,
        related_name="user_settings",
        verbose_name="Критерий",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    class Meta:
        verbose_name = "Настройки критерия"
        verbose_name_plural = "Настройки критериев"
        unique_together = [["user", "criterion"]]

    def __str__(self) -> str:
        status = "вкл" if self.is_active else "выкл"
        return f"{self.user} — {self.criterion.name} [{status}]"

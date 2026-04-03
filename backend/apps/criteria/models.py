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

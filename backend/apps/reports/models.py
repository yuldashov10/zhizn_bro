from django.db import models

from apps.candidates.models import Candidate
from apps.users.models import User


class ReportLog(models.Model):
    """
    Лог сгенерированных отчётов.
    Хранит метаданные отчёта и путь к файлу если он был создан.
    """

    class ReportType(models.TextChoices):
        TEXT = "text", "Текст в боте"
        PDF = "pdf", "PDF"
        EXCEL = "excel", "Excel"
        PNG = "png", "PNG"

    class Trigger(models.TextChoices):
        MANUAL = "manual", "По запросу"
        AUTO_WEEKLY = "auto_weekly", "Автоматически (еженедельно)"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="Пользователь",
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name="Кандидат",
    )
    report_type = models.CharField(
        max_length=10,
        choices=ReportType.choices,
        verbose_name="Тип отчёта",
    )
    trigger = models.CharField(
        max_length=20,
        choices=Trigger.choices,
        default=Trigger.MANUAL,
        verbose_name="Причина генерации",
    )
    file = models.FileField(
        upload_to="reports/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Файл отчёта",
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время генерации",
    )

    class Meta:
        verbose_name = "Лог отчёта"
        verbose_name_plural = "Логи отчётов"
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        candidate_info = f" | {self.candidate}" if self.candidate else ""
        return (
            f"[{self.get_report_type_display()}] "
            f"{self.user}{candidate_info} "
            f"[{self.generated_at:%d.%m.%Y %H:%M}]"
        )

    def has_file(self) -> bool:
        """Проверяет прикреплён ли файл к отчёту."""
        return bool(self.file)

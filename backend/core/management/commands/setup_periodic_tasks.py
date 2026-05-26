import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    """
    Создаёт периодические Celery задачи в БД.
    Идемпотентна — безопасно запускать повторно.
    Запускать после деплоя: make setup_tasks
    """

    help = "Настроить периодические задачи Celery Beat"

    def handle(self, *args, **options) -> None:
        self.stdout.write("Настройка периодических задач...")

        self._setup_reports_tasks()
        self._setup_token_tasks()

        self.stdout.write(
            self.style.SUCCESS("Периодические задачи успешно настроены!")
        )

    def _setup_reports_tasks(self) -> None:
        """Задачи для отчётов."""
        weekly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="9",
            day_of_week="1",
            day_of_month="*",
            month_of_year="*",
        )
        PeriodicTask.objects.update_or_create(
            name="Еженедельная генерация отчётов",
            defaults={
                "task": "apps.reports.tasks.weekly_reports_task",
                "crontab": weekly_schedule,
                "enabled": True,
                "args": json.dumps([]),
            },
        )
        self.stdout.write("  ✅ Еженедельные отчёты (пн 09:00 UTC)")

        cleanup_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="3",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        PeriodicTask.objects.update_or_create(
            name="Очистка старых отчётов",
            defaults={
                "task": "apps.reports.tasks.cleanup_old_reports_task",
                "crontab": cleanup_schedule,
                "enabled": True,
                "args": json.dumps([]),
            },
        )
        self.stdout.write("  ✅ Очистка отчётов (ежедневно 03:00 UTC)")

    def _setup_token_tasks(self) -> None:
        """Задачи для сброса токенов."""
        daily_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        PeriodicTask.objects.update_or_create(
            name="Ежедневный сброс токенов",
            defaults={
                "task": "apps.users.tasks.reset_daily_tokens_task",
                "crontab": daily_schedule,
                "enabled": True,
                "args": json.dumps([]),
            },
        )
        self.stdout.write("  ✅ Сброс дневных токенов (ежедневно 00:00 UTC)")

        monthly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",
            day_of_week="*",
            day_of_month="1",
            month_of_year="*",
        )
        PeriodicTask.objects.update_or_create(
            name="Месячный сброс токенов",
            defaults={
                "task": "apps.users.tasks.reset_monthly_tokens_task",
                "crontab": monthly_schedule,
                "enabled": True,
                "args": json.dumps([]),
            },
        )
        self.stdout.write("  ✅ Сброс месячных токенов (1-е число 00:00 UTC)")

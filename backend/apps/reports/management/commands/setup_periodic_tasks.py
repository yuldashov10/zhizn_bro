import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    """
    Создаёт периодические Celery задачи в БД.
    Запускать один раз после деплоя: make setup_tasks
    """

    help = "Настроить периодические задачи Celery Beat"

    def handle(self, *args, **options):
        self.stdout.write("Настройка периодических задач...")

        # Еженедельные отчёты — каждый понедельник в 09:00 UTC
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

        # Ежедневная очистка старых отчётов — каждый день в 03:00 UTC
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

        self.stdout.write(
            self.style.SUCCESS("Периодические задачи успешно настроены!")
        )

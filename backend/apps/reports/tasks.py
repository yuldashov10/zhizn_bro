import logging

from celery import shared_task

from apps.candidates.models import Candidate
from apps.reports.models import ReportLog
from apps.reports.services.report import ReportService

logger = logging.getLogger("apps.reports")


@shared_task
def generate_report_task(report_id: int) -> None:
    """Асинхронная генерация отчёта через Celery."""
    try:
        report = ReportLog.objects.get(pk=report_id)
        ReportService.generate(report)
    except ReportLog.DoesNotExist:
        logger.error(f"ReportLog {report_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка генерации отчёта {report_id}: {e}")
        raise


@shared_task
def weekly_reports_task() -> None:
    """
    Еженедельная задача — генерирует отчёты для всех активных кандидатов.
    Запускается через Celery Beat.
    """
    from apps.users.models import User

    users = User.objects.filter(is_active=True, is_superuser=False)
    count = 0

    for user in users:
        candidates = Candidate.objects.filter(
            user=user,
            is_active=True,
        )
        for candidate in candidates:
            report = ReportLog.objects.create(
                user=user,
                candidate=candidate,
                report_type=ReportLog.ReportType.PDF,
                trigger=ReportLog.Trigger.AUTO_WEEKLY,
            )
            generate_report_task.delay(report.pk)
            count += 1

    logger.info(f"Запущена генерация {count} еженедельных отчётов")

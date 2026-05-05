import logging

from celery import shared_task
from constance import config
from django.utils import timezone

from apps.candidates.models import Candidate
from apps.reports.models import ReportLog
from apps.reports.services.report import ReportService

logger = logging.getLogger("apps.reports")


@shared_task
def generate_report_task(
    report_id: int,
    photo_bytes: bytes | None = None,
) -> None:
    """
    Асинхронная генерация отчёта через Celery.

    Args:
        report_id:   ID записи ReportLog
        photo_bytes: байты фото кандидата (опционально)
    """
    try:
        report = ReportLog.objects.get(pk=report_id)
        ReportService.generate(report, photo_bytes=photo_bytes)
        logger.info(f"Отчёт {report_id} успешно сгенерирован")
    except ReportLog.DoesNotExist:
        logger.error(f"ReportLog {report_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка генерации отчёта {report_id}: {e}")
        raise


@shared_task
def cleanup_old_reports_task() -> None:
    """
    Удаляет файлы отчётов старше REPORT_RETENTION_DAYS дней.
    Запись в БД сохраняется, удаляется только файл.
    Минимальный срок хранения — 1 день.
    """
    retention_days = max(1, config.REPORT_RETENTION_DAYS)
    cutoff_date = timezone.now() - timezone.timedelta(days=retention_days)

    old_reports = (
        ReportLog.objects.filter(
            generated_at__lt=cutoff_date,
        )
        .exclude(file="")
        .exclude(file__isnull=True)
    )

    deleted_count = 0
    error_count = 0

    for report in old_reports:
        try:
            if report.file:
                report.file.delete(save=False)
            report.file = None
            report.save(update_fields=["file"])
            deleted_count += 1
        except Exception as e:
            logger.error(f"Ошибка удаления файла отчёта {report.pk}: {e}")
            error_count += 1

    logger.info(
        f"Очистка отчётов завершена: "
        f"удалено {deleted_count} файлов, "
        f"ошибок {error_count}, "
        f"срок хранения {retention_days} дней"
    )


@shared_task
def weekly_reports_task() -> None:
    """
    Еженедельная задача — генерирует PDF отчёты для всех
    активных кандидатов всех пользователей.
    Запускается только если WEEKLY_REPORTS_ENABLED=True.
    """
    if not config.WEEKLY_REPORTS_ENABLED:
        logger.info("Еженедельные отчёты отключены в настройках")
        return

    from apps.users.models import User

    users = User.objects.filter(is_active=True, is_superuser=False)
    count = 0

    for user in users:
        candidates = Candidate.objects.filter(
            user=user,
            is_active=True,
        )
        for candidate in candidates:
            if not candidate.events.exists():
                continue  # Пропускаем кандидатов без событий

            report = ReportLog.objects.create(
                user=user,
                candidate=candidate,
                report_type=ReportLog.ReportType.PDF,
                trigger=ReportLog.Trigger.AUTO_WEEKLY,
            )
            generate_report_task.delay(report.pk)
            count += 1

    logger.info(f"Запущена генерация {count} еженедельных отчётов")

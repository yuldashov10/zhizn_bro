import logging

from celery import shared_task
from django.utils import timezone

from apps.users.models import UserTokenLimit

logger = logging.getLogger("apps.users")


@shared_task
def reset_daily_tokens_task() -> None:
    """
    Сбрасывает дневной счётчик токенов для всех пользователей.
    Запускается каждый день в 00:00 UTC.
    """
    now = timezone.now()
    updated = UserTokenLimit.objects.update(
        used_today=0,
        reset_at=now,
    )
    logger.info(f"Сброс дневных токенов: обновлено {updated} записей")


@shared_task
def reset_monthly_tokens_task() -> None:
    """
    Сбрасывает месячный счётчик токенов для всех пользователей.
    Запускается 1-го числа каждого месяца в 00:00 UTC.
    """
    now = timezone.now()
    updated = UserTokenLimit.objects.update(
        used_today=0,
        used_this_month=0,
        reset_at=now,
    )
    logger.info(f"Сброс месячных токенов: обновлено {updated} записей")

import logging

from core.notifications import notifier

logger = logging.getLogger("core.sentry")


class SentryTelegramHandler(logging.Handler):
    """
    Logging handler который отправляет CRITICAL ошибки
    в Telegram дополнительно к Sentry.
    """

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.CRITICAL:
            try:
                notifier.notify_error(
                    error=Exception(self.format(record)),
                    context=f"{record.name} "
                    f"[{record.filename}:{record.lineno}]",
                )
            except Exception as e:
                logger.error(f"Ошибка SentryTelegramHandler: {e}")

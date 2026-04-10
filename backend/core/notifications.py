import logging
from datetime import datetime

import httpx
from constance import config
from decouple import config as env_config

logger = logging.getLogger("core.notifications")


class TelegramNotifier:
    """
    Отправляет уведомления администратору в Telegram.
    Используется для критических ошибок и событий системы.
    """

    def __init__(self) -> None:
        self._token = env_config("BOT_TOKEN", default="")
        self._chat_id_env = env_config("ADMIN_TELEGRAM_ID", default="")
        self._base_url = f"https://api.telegram.org/bot{self._token}"

    @property
    def _chat_id(self) -> str:
        try:

            return config.ADMIN_TELEGRAM_ID or self._chat_id_env
        except Exception:
            return self._chat_id_env

    @property
    def _is_configured(self) -> bool:
        """Проверяет настроены ли токен и chat_id."""
        return bool(self._token and self._chat_id)

    def send(self, message: str) -> bool:
        """
        Отправляет сообщение администратору.

        Args:
            message: текст сообщения (поддерживает HTML)

        Returns:
            bool: True если успешно отправлено
        """
        if not self._is_configured:
            logger.warning("TelegramNotifier не настроен — пропускаем")
            return False

        try:
            response = httpx.post(
                f"{self._base_url}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
                timeout=10.0,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка отправки Telegram уведомления: {e}")
            return False

    def notify_error(
        self,
        error: Exception,
        context: str = "",
    ) -> bool:
        """
        Отправляет уведомление об ошибке.

        Args:
            error:   исключение
            context: контекст где произошла ошибка

        Returns:
            bool: True если успешно отправлено
        """
        message = (
            f"🚨 <b>Ошибка в Жизнь БРО</b>\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"📍 Контекст: {context or '—'}\n"
            "❌ Ошибка: "
            f"<code>{type(error).__name__}: {str(error)[:200]}</code>"
        )
        return self.send(message)

    def notify_service_down(self, service: str, reason: str = "") -> bool:
        """
        Уведомляет о недоступности сервиса.

        Args:
            service: название сервиса
            reason:  причина недоступности

        Returns:
            bool: True если успешно отправлено
        """
        message = (
            f"⚠️ <b>Сервис недоступен</b>\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"🔧 Сервис: <b>{service}</b>\n"
            f"📝 Причина: {reason or '—'}"
        )
        return self.send(message)

    def notify_service_up(self, service: str) -> bool:
        """
        Уведомляет о восстановлении сервиса.

        Args:
            service: название сервиса

        Returns:
            bool: True если успешно отправлено
        """
        message = (
            f"✅ <b>Сервис восстановлен</b>\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"🔧 Сервис: <b>{service}</b>"
        )
        return self.send(message)


notifier = TelegramNotifier()

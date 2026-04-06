import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.client.api import APIError, BROApiClient

logger = logging.getLogger("bot")


class AuthMiddleware(BaseMiddleware):
    """
    Middleware авторизации пользователя.
    При каждом запросе проверяет наличие токена.
    Если пользователь новый — регистрирует его через API.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        token = await self._get_or_create_token(
            telegram_id=user.id,
            username=user.username,
        )

        # Передаём клиент с токеном в хендлер
        data["api"] = BROApiClient(token=token)
        data["token"] = token

        try:
            return await handler(event, data)
        finally:
            await data["api"].close()

    async def _get_or_create_token(
        self,
        telegram_id: int,
        username: str | None,
    ) -> str:
        """Получает или создаёт токен пользователя."""
        client = BROApiClient()
        try:
            response = await client.auth_telegram(
                telegram_id=telegram_id,
                username=username,
            )
            return response["token"]
        except APIError as e:
            logger.error(f"Ошибка авторизации {telegram_id}: {e}")
            raise
        finally:
            await client.close()

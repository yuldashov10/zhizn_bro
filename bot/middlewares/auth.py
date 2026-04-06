import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.client.api import APIError, BROApiClient

logger = logging.getLogger("bot")

_token_cache: dict[int, str] = {}


class AuthMiddleware(BaseMiddleware):
    """
    Middleware авторизации пользователя.
    Кэширует токен в памяти чтобы не делать
    запрос к API при каждом сообщении.
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
        """
        Возвращает токен из кэша или запрашивает новый.
        """
        if telegram_id in _token_cache:
            return _token_cache[telegram_id]

        client = BROApiClient()
        try:
            response = await client.auth_telegram(
                telegram_id=telegram_id,
                username=username,
            )
            token = response["token"]
            _token_cache[telegram_id] = token
            logger.info(f"Токен получен для {telegram_id}")
            return token
        except APIError as e:
            logger.error(f"Ошибка авторизации {telegram_id}: {e}")
            raise
        finally:
            await client.close()

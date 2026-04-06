import logging

from aiogram import F, Router
from aiogram.types import Message

from bot.client.api import APIError, BROApiClient
from bot.messages.ru import ERROR_GENERAL

logger = logging.getLogger("bot")
router = Router()


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(
    message: Message,
    api: BROApiClient,
) -> None:
    """Показывает настройки пользователя."""
    try:
        user = await api.get_me()
        token_limit = await api.get_token_limit()
        profile = user.get("profile", {})

        attachment = profile.get("attachment_type_display") or "Не определён"
        tier = token_limit.get("tier_display", "—")
        used_today = token_limit.get("used_today", 0)
        daily_limit = token_limit.get("daily_limit", 0)
        used_month = token_limit.get("used_this_month", 0)
        monthly_limit = token_limit.get("monthly_limit", 0)

        text = (
            f"⚙️ <b>Настройки</b>\n\n"
            f"<b>Профиль:</b>\n"
            f"Тип привязанности: {attachment}\n"
            f"Источник: {profile.get('attachment_source_display') or '—'}\n\n"
            f"<b>Токены:</b>\n"
            f"Тариф: {tier}\n"
            f"Использовано сегодня: {used_today} / {daily_limit}\n"
            f"Использовано в месяц: {used_month} / {monthly_limit}\n"
        )

        await message.answer(text, parse_mode="HTML")

    except APIError:
        await message.answer(ERROR_GENERAL)

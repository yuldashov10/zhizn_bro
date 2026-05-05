import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.client.api import BROApiClient
from bot.keyboards.reply import get_main_menu
from bot.messages.ru import ALREADY_REGISTERED, WELCOME

logger = logging.getLogger("bot")
router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    api: BROApiClient,
    is_new_user: bool,
) -> None:
    """Обработчик команды /start."""
    if is_new_user:
        await message.answer(
            WELCOME,
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )
        logger.info(f"Новый пользователь {message.from_user.id}")
    else:
        await message.answer(
            ALREADY_REGISTERED,
            reply_markup=get_main_menu(),
        )
        logger.info(f"Пользователь {message.from_user.id} вернулся")

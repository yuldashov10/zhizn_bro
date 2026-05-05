import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.client.api import BROApiClient
from bot.keyboards.inline import get_tests_menu
from bot.keyboards.reply import get_main_menu

logger = logging.getLogger("bot")
router = Router()

COMING_SOON = (
    "🚧 <b>Скоро!</b>\n\n"
    "Этот тест находится в разработке.\n"
    "Следи за обновлениями 👉 @zhizn_bro_news"
)


@router.message(F.text == "🧪 Тесты")
async def tests_menu_handler(message: Message) -> None:
    """Показывает меню доступных тестов."""
    await message.answer(
        "🧪 <b>Тесты</b>\n\n" "Выбери тест который хочешь пройти:",
        reply_markup=get_tests_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "tests:attachment")
async def test_attachment_handler(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Переход к тесту привязанности."""
    from bot.handlers.assessments import assessment_start

    await callback.message.answer(
        "Переходим к тесту привязанности:",
        reply_markup=get_main_menu(),
    )
    await assessment_start(callback.message, state, api)
    await callback.answer()


@router.callback_query(F.data == "tests:temperament")
async def test_temperament_handler(callback: CallbackQuery) -> None:
    """Тест темперамента — в разработке."""
    await callback.message.answer(COMING_SOON, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "tests:love_languages")
async def test_love_languages_handler(callback: CallbackQuery) -> None:
    """Тест любовных языков — в разработке."""
    await callback.message.answer(COMING_SOON, parse_mode="HTML")
    await callback.answer()

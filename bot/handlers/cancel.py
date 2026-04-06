from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.reply import get_main_menu
from bot.messages.ru import CANCEL

router = Router()


@router.callback_query(F.data == "cancel")
async def cancel_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Отмена через inline кнопку."""
    await state.clear()
    await callback.message.answer(CANCEL, reply_markup=get_main_menu())
    await callback.answer()


@router.message(F.text == "❌ Отмена")
async def cancel_message(
    message: Message,
    state: FSMContext,
) -> None:
    """Отмена через reply кнопку."""
    await state.clear()
    await message.answer(CANCEL, reply_markup=get_main_menu())

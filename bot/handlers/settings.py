import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.client.api import APIError, BROApiClient
from bot.keyboards.inline import (
    get_criteria_keyboard,
    get_hard_stops_keyboard,
    get_settings_menu,
)
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu
from bot.messages.ru import CANCEL, ERROR_GENERAL
from bot.states.fsm import SettingsStates

logger = logging.getLogger("bot")
router = Router()


# ── Главное меню настроек ─────────────────────────────────────────────────────


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(
    message: Message,
    api: BROApiClient,
) -> None:
    """Показывает меню настроек."""
    try:
        user = await api.get_me()
        token_limit = await api.get_token_limit()
        profile = user.get("profile", {})

        attachment = profile.get("attachment_type_display") or "Не определён"
        attachment_source = profile.get("attachment_source_display") or "—"
        tier = token_limit.get("tier_display", "—")
        used_today = token_limit.get("used_today", 0)
        daily_limit = token_limit.get("daily_limit", 0)
        used_month = token_limit.get("used_this_month", 0)
        monthly_limit = token_limit.get("monthly_limit", 0)

        text = (
            f"⚙️ <b>Настройки</b>\n\n"
            f"<b>Профиль:</b>\n"
            f"Тип привязанности: <b>{attachment}</b>\n"
            f"Источник: {attachment_source}\n\n"
            f"<b>Токены:</b>\n"
            f"Тариф: {tier}\n"
            f"Использовано сегодня: {used_today} / {daily_limit}\n"
            f"Использовано в месяц: {used_month} / {monthly_limit}\n"
        )
        await message.answer(
            text,
            reply_markup=get_settings_menu(),
            parse_mode="HTML",
        )
    except APIError:
        await message.answer(ERROR_GENERAL)


@router.callback_query(F.data == "settings:back")
async def settings_back_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    """Возврат в главное меню настроек."""
    await callback.message.edit_reply_markup(
        reply_markup=get_settings_menu(),
    )
    await callback.answer()


# ── Hard Stops ────────────────────────────────────────────────────────────────


@router.callback_query(F.data == "settings:hard_stops")
async def hard_stops_settings_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    try:
        hard_stops = await api.get_hard_stops()
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_hard_stops_keyboard(hard_stops),
            )
        except Exception:
            pass
        await callback.answer()
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
        await callback.answer()


@router.callback_query(F.data.startswith("hs_toggle:"))
async def hard_stop_toggle_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    hs_id = int(callback.data.split(":")[1])
    try:
        result = await api.toggle_hard_stop(hs_id)
        hard_stops = await api.get_hard_stops()
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_hard_stops_keyboard(hard_stops),
            )
        except Exception:
            pass
        # Показываем статус в коротком уведомлении
        is_active = result.get("is_active", True)
        await callback.answer("Включён ✅" if is_active else "Выключен ❌")
    except APIError:
        await callback.answer(ERROR_GENERAL)


@router.callback_query(F.data == "hs_suggest")
async def hard_stop_suggest_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начинает диалог предложения нового Hard Stop."""
    await state.set_state(SettingsStates.suggesting_hs)
    await callback.message.answer(
        "💡 Опиши Hard Stop который хочешь предложить.\n\n"
        "<i>Например: «Употребляет наркотики»</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.suggesting_hs)
async def hard_stop_suggest_handler(
    message: Message,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Сохраняет предложение Hard Stop."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(CANCEL, reply_markup=get_main_menu())
        return

    try:
        await api.suggest_hard_stop(message.text.strip())
        await state.clear()
        await message.answer(
            "✅ Спасибо! Твоё предложение отправлено на рассмотрение.\n"
            "Если оно подойдёт — добавим в систему.",
            reply_markup=get_main_menu(),
        )
    except APIError as e:
        if "400" in str(e):
            await message.answer(
                "❌ Описание слишком короткое. Напиши подробнее (минимум 10 символов)."
            )
        else:
            await message.answer(ERROR_GENERAL)


# ── Критерии ──────────────────────────────────────────────────────────────────


@router.callback_query(F.data == "settings:criteria")
async def criteria_settings_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    try:
        criteria = await api.get_criteria()
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_criteria_keyboard(criteria),
            )
        except Exception:
            pass
        await callback.answer()
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
        await callback.answer()


@router.callback_query(F.data.startswith("cr_toggle:"))
async def criterion_toggle_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    cr_id = int(callback.data.split(":")[1])
    try:
        result = await api.toggle_criterion(cr_id)
        criteria = await api.get_criteria()
        try:
            await callback.message.edit_reply_markup(
                reply_markup=get_criteria_keyboard(criteria),
            )
        except Exception:
            pass
        is_active = result.get("is_active", True)
        await callback.answer("Включён ✅" if is_active else "Выключен ❌")
    except APIError as e:
        if "400" in str(e):
            await callback.answer(
                "❌ Нельзя отключить — минимум 3 критерия",
                show_alert=True,
            )
        else:
            await callback.answer(ERROR_GENERAL)


# ── Тест привязанности из настроек ────────────────────────────────────────────


@router.callback_query(F.data == "settings:test")
async def settings_test_handler(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Переход к тесту привязанности из настроек."""
    from bot.handlers.assessments import assessment_start

    await callback.message.answer(
        "Переходим к тесту привязанности:",
        reply_markup=get_main_menu(),
    )
    await assessment_start(callback.message, state, api)
    await callback.answer()

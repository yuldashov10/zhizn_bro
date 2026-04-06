import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.client.api import APIError, BROApiClient
from bot.keyboards.inline import get_candidates_inline, get_score_confirm
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu
from bot.messages.ru import (
    CANCEL,
    ERROR_GENERAL,
    ERROR_TEXT_TOO_SHORT,
    EVENT_ADDED,
    EVENT_AI_SCORE,
    EVENT_ANALYZING,
    EVENT_BIAS_WARNING,
    EVENT_CANDIDATE_REQUEST,
    EVENT_HARD_STOP,
    EVENT_TEXT_REQUEST,
)
from bot.states.fsm import EventStates

logger = logging.getLogger("bot")
router = Router()


@router.message(F.text == "📝 Добавить событие")
async def add_event_start(
    message: Message,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Начинает диалог добавления события."""
    try:
        candidates = await api.get_candidates(is_active=True)
        if not candidates:
            await message.answer(
                "У тебя нет активных кандидатов. Сначала добавь кандидата.",
                reply_markup=get_main_menu(),
            )
            return
        await state.set_state(EventStates.waiting_for_candidate)
        await state.update_data(candidates=candidates)
        await message.answer(
            EVENT_CANDIDATE_REQUEST,
            reply_markup=get_candidates_inline(candidates),
        )
    except APIError:
        await message.answer(ERROR_GENERAL)


@router.callback_query(F.data.startswith("event:add:"))
async def add_event_from_candidate(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Добавить событие из карточки кандидата."""
    candidate_id = int(callback.data.split(":")[2])
    try:
        candidate = await api.get_candidate(candidate_id)
        await state.set_state(EventStates.waiting_for_text)
        await state.update_data(
            candidate_id=candidate_id,
            candidate_name=candidate["name"],
        )
        await callback.message.answer(
            EVENT_TEXT_REQUEST,
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
    finally:
        await callback.answer()


@router.callback_query(
    EventStates.waiting_for_candidate,
    F.data.startswith("candidate:"),
)
async def event_candidate_selected(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Пользователь выбрал кандидата для события."""
    candidate_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    candidate = next(
        (c for c in data["candidates"] if c["id"] == candidate_id),
        None,
    )
    if not candidate:
        await callback.answer("Кандидат не найден")
        return

    await state.update_data(
        candidate_id=candidate_id,
        candidate_name=candidate["name"],
    )
    await state.set_state(EventStates.waiting_for_text)
    await callback.message.answer(
        EVENT_TEXT_REQUEST,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(EventStates.waiting_for_text)
async def event_text_handler(
    message: Message,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Получает текст события и запускает AI анализ."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(CANCEL, reply_markup=get_main_menu())
        return

    if len(message.text.strip()) < 10:
        await message.answer(ERROR_TEXT_TOO_SHORT)
        return

    data = await state.get_data()
    analyzing_msg = await message.answer(EVENT_ANALYZING)

    try:
        event = await api.create_event(
            candidate_id=data["candidate_id"],
            raw_text=message.text.strip(),
        )
        await analyzing_msg.delete()

        # Показываем результаты анализа по каждому критерию
        scores = event.get("scores", [])
        if scores:
            await state.update_data(
                event_id=event["id"],
                scores=scores,
                current_score_index=0,
            )
            await state.set_state(EventStates.confirming_ai_score)
            await _show_next_score(message, state)
        else:
            await state.clear()
            await message.answer(
                EVENT_ADDED,
                reply_markup=get_main_menu(),
            )

        # Показываем предупреждение если есть
        if event.get("bias_warning"):
            await message.answer(
                EVENT_BIAS_WARNING.format(warning=event["bias_warning"]),
                parse_mode="HTML",
            )

        # Показываем Hard Stop если сработал
        if event.get("is_hard_stop"):
            hard_stop_log = event.get("hard_stop_logs", [{}])[0]
            await message.answer(
                EVENT_HARD_STOP.format(
                    hard_stop=hard_stop_log.get("hard_stop_name", "Неизвестно")
                ),
                parse_mode="HTML",
            )

    except APIError as e:
        await analyzing_msg.delete()
        logger.error(f"Ошибка создания события: {e}")
        await message.answer(ERROR_GENERAL, reply_markup=get_main_menu())
        await state.clear()


@router.callback_query(
    EventStates.confirming_ai_score,
    F.data.startswith("score:"),
)
async def score_confirm_handler(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Обрабатывает подтверждение или корректировку оценки ИИ."""
    parts = callback.data.split(":")
    action = parts[1]
    event_id = int(parts[2])
    criterion_id = int(parts[3])
    score = int(parts[4])

    try:
        if action == "confirm":
            await api.confirm_score(
                event_id=event_id,
                criterion_id=criterion_id,
                is_confirmed=True,
            )
        else:
            await api.confirm_score(
                event_id=event_id,
                criterion_id=criterion_id,
                user_score=score,
                is_confirmed=True,
            )
    except APIError:
        await callback.answer("Ошибка сохранения оценки")

    await callback.answer("✅ Оценка сохранена")

    # Показываем следующий критерий
    data = await state.get_data()
    next_index = data["current_score_index"] + 1
    await state.update_data(current_score_index=next_index)

    if next_index < len(data["scores"]):
        await _show_next_score(callback.message, state)
    else:
        await state.clear()
        await callback.message.answer(
            EVENT_ADDED,
            reply_markup=get_main_menu(),
        )


async def _show_next_score(
    message: Message,
    state: FSMContext,
) -> None:
    """Показывает следующую оценку критерия для подтверждения."""
    data = await state.get_data()
    index = data["current_score_index"]
    score_data = data["scores"][index]

    await message.answer(
        EVENT_AI_SCORE.format(
            criterion=score_data["criterion_name"],
            score=score_data["ai_score"],
            reasoning=score_data.get("reasoning", ""),
        ),
        reply_markup=get_score_confirm(
            event_id=data["event_id"],
            criterion_id=score_data["criterion"],
            ai_score=score_data["ai_score"],
        ),
        parse_mode="HTML",
    )

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.client.api import APIError, BROApiClient
from bot.keyboards.inline import (
    get_candidate_actions,
    get_candidates_inline,
    get_status_keyboard,
)
from bot.keyboards.reply import (
    get_cancel_keyboard,
    get_confirm_keyboard,
    get_main_menu,
    get_skip_keyboard,
)
from bot.messages.ru import (
    CANCEL,
    CANDIDATE_ADDED,
    CANDIDATE_AGE_REQUEST,
    CANDIDATE_ARCHIVED,
    CANDIDATE_LIST_EMPTY,
    CANDIDATE_MET_AT_REQUEST,
    CANDIDATE_NAME_REQUEST,
    CANDIDATE_NOT_FOUND,
    CANDIDATE_PHOTO_REQUEST,
    ERROR_GENERAL,
    ERROR_INVALID_AGE,
    SCORE_NO_EVENTS,
    SCORE_RESULT,
)
from bot.states.fsm import CandidateStates, CandidateStatusStates

logger = logging.getLogger("bot")
router = Router()


@router.message(F.text == "👤 Кандидаты")
async def candidates_menu_handler(
    message: Message,
) -> None:
    """Открывает меню кандидатов."""
    from bot.keyboards.reply import get_candidates_menu

    await message.answer(
        "Управление кандидатами:",
        reply_markup=get_candidates_menu(),
    )


# ── Список кандидатов ───────────────────────────────────────────────────────


@router.message(F.text == "📋 Список кандидатов")
async def candidates_list_handler(
    message: Message,
    api: BROApiClient,
) -> None:
    """Показывает список активных кандидатов."""
    try:
        candidates = await api.get_candidates(is_active=True)
        if not candidates:
            await message.answer(CANDIDATE_LIST_EMPTY)
            return
        await message.answer(
            "👤 Выбери кандидата:",
            reply_markup=get_candidates_inline(candidates),
        )
    except APIError:
        await message.answer(ERROR_GENERAL)


@router.callback_query(F.data.startswith("candidate:score:"))
async def candidate_score_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    """Показывает скор кандидата."""
    candidate_id = int(callback.data.split(":")[2])
    try:
        data = await api.get_candidate_score(candidate_id)
        score = data.get("score")

        if score is None:
            await callback.message.answer(SCORE_NO_EVENTS)
        else:
            score_bar = _build_score_bar(score)
            await callback.message.answer(
                SCORE_RESULT.format(
                    name=data["candidate_name"],
                    score_display=f"{score_bar} {score}/100",
                    events_count=data["events_count"],
                ),
                parse_mode="HTML",
            )
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("candidate:history:"))
async def candidate_history_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    """Показывает историю статусов кандидата."""
    candidate_id = int(callback.data.split(":")[2])
    try:
        history = await api.get_status_history(candidate_id)
        if not history:
            await callback.message.answer("История статусов пуста.")
            await callback.answer()
            return

        lines = ["📋 <b>История статусов:</b>\n"]
        for item in history:
            lines.append(
                f"• {item['status_display']} — "
                f"{item['started_at'][:10]}"
                + (f"\n  <i>{item['note']}</i>" if item.get("note") else "")
            )
        await callback.message.answer(
            "\n".join(lines),
            parse_mode="HTML",
        )
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("candidate:archive:"))
async def candidate_archive_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    """Архивирует кандидата."""
    candidate_id = int(callback.data.split(":")[2])
    try:
        await api.archive_candidate(candidate_id)
        await callback.message.answer(
            CANDIDATE_ARCHIVED,
            reply_markup=get_main_menu(),
        )
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("candidate:status:"))
async def candidate_status_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Открывает меню смены статуса."""
    candidate_id = int(callback.data.split(":")[2])
    await state.set_state(CandidateStatusStates.choosing_status)
    await state.update_data(candidate_id=candidate_id)
    await callback.message.answer(
        "Выбери новый статус:",
        reply_markup=get_status_keyboard(),
    )
    await callback.answer()


@router.callback_query(
    CandidateStatusStates.choosing_status,
    F.data.startswith("status:"),
)
async def status_selected_handler(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Обрабатывает выбор нового статуса."""
    status = callback.data.split(":")[1]
    data = await state.get_data()
    candidate_id = data["candidate_id"]  # noqa: skip

    await state.set_state(CandidateStatusStates.waiting_for_note)
    await state.update_data(status=status)

    await callback.message.answer(
        "Добавь примечание к смене статуса (или нажми «Пропустить»):",
        reply_markup=get_skip_keyboard(),
    )
    await callback.answer()


@router.message(CandidateStatusStates.waiting_for_note)
async def status_note_handler(
    message: Message,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Сохраняет новый статус с примечанием."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(CANCEL, reply_markup=get_main_menu())
        return

    note = "" if message.text == "⏭ Пропустить" else message.text.strip()
    data = await state.get_data()

    try:
        await api.update_status(
            candidate_id=data["candidate_id"],
            status=data["status"],
            note=note,
        )
        await state.clear()

        status_display = {
            "meeting": "Знакомство",
            "dating": "Встречаемся",
            "serious": "Серьёзно",
            "pause": "Пауза",
            "ended": "Завершено",
        }.get(data["status"], data["status"])

        await message.answer(
            f"✅ Статус изменён на <b>{status_display}</b>",
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )
    except APIError:
        await message.answer(ERROR_GENERAL, reply_markup=get_main_menu())
        await state.clear()


@router.callback_query(
    F.data.startswith("candidate:")
    & ~F.data.contains(":score:")
    & ~F.data.contains(":archive:")
    & ~F.data.contains(":history:")
    & ~F.data.contains(":status:")
)
async def candidate_detail_handler(
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    """Показывает детали кандидата с кнопками действий."""
    candidate_id = int(callback.data.split(":")[1])
    try:
        candidate = await api.get_candidate(candidate_id)
        score_data = await api.get_candidate_score(candidate_id)
        score = score_data.get("score")
        score_text = f"{score}/100" if score is not None else "нет данных"

        text = (
            f"👤 <b>{candidate['name']}</b>\n"
            f"Возраст: {candidate.get('age') or '—'}\n"
            f"Познакомились: {candidate.get('met_at') or '—'}\n"
            f"Тип привязанности: "
            f"{candidate.get('ai_attachment_type_display') or '—'}\n"
            f"📊 Скор: {score_text}"
        )
        await callback.message.answer(
            text,
            reply_markup=get_candidate_actions(candidate_id),
            parse_mode="HTML",
        )
    except APIError:
        await callback.message.answer(CANDIDATE_NOT_FOUND)
    finally:
        await callback.answer()


# ── Добавление кандидата ────────────────────────────────────────────────────


@router.message(F.text == "➕ Добавить кандидата")
async def add_candidate_start(
    message: Message,
    state: FSMContext,
) -> None:
    """Начинает диалог добавления кандидата."""
    await state.set_state(CandidateStates.waiting_for_name)
    await message.answer(
        CANDIDATE_NAME_REQUEST,
        reply_markup=get_cancel_keyboard(),
    )


@router.message(CandidateStates.waiting_for_name)
async def candidate_name_handler(
    message: Message,
    state: FSMContext,
) -> None:
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(CandidateStates.waiting_for_age)
    await message.answer(
        CANDIDATE_AGE_REQUEST,
        reply_markup=get_skip_keyboard(),
    )


@router.message(CandidateStates.waiting_for_age)
async def candidate_age_handler(
    message: Message,
    state: FSMContext,
) -> None:
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    age = None
    if message.text != "⏭ Пропустить":
        try:
            age = int(message.text)
            if not 16 <= age <= 80:
                raise ValueError
        except ValueError:
            await message.answer(ERROR_INVALID_AGE)
            return

    await state.update_data(age=age)
    await state.set_state(CandidateStates.waiting_for_met_at)
    await message.answer(
        CANDIDATE_MET_AT_REQUEST,
        reply_markup=get_skip_keyboard(),
    )


@router.message(CandidateStates.waiting_for_met_at)
async def candidate_met_at_handler(
    message: Message,
    state: FSMContext,
) -> None:
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    met_at = None if message.text == "⏭ Пропустить" else message.text.strip()
    await state.update_data(met_at=met_at)
    await state.set_state(CandidateStates.waiting_for_photo)
    await message.answer(
        CANDIDATE_PHOTO_REQUEST,
        reply_markup=get_skip_keyboard(),
    )


@router.message(CandidateStates.waiting_for_photo)
async def candidate_photo_handler(
    message: Message,
    state: FSMContext,
) -> None:
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    telegram_photo_id = None
    if message.photo:
        # Берём самое большое фото (последнее в списке)
        telegram_photo_id = message.photo[-1].file_id

    await state.update_data(telegram_photo_id=telegram_photo_id)
    await state.set_state(CandidateStates.confirming)

    data = await state.get_data()
    has_photo = telegram_photo_id is not None
    text = (
        f"📋 <b>Проверь данные:</b>\n\n"
        f"Имя: <b>{data['name']}</b>\n"
        f"Возраст: {data.get('age') or '—'}\n"
        f"Познакомились: {data.get('met_at') or '—'}\n"
        f"Фото: {'✅ Есть' if has_photo else '—'}\n"
    )
    await message.answer(
        text,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML",
    )


@router.message(CandidateStates.confirming)
async def candidate_confirm_handler(
    message: Message,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    if message.text == "❌ Отмена":
        await _cancel(message, state)
        return

    if message.text != "✅ Подтвердить":
        return

    data = await state.get_data()
    try:
        candidate = await api.create_candidate(
            name=data["name"],
            age=data.get("age"),
            met_at=data.get("met_at") or "",
            telegram_photo_id=data.get("telegram_photo_id"),
        )
        await state.clear()
        await message.answer(
            CANDIDATE_ADDED.format(name=candidate["name"]),
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )
    except APIError:
        await message.answer(ERROR_GENERAL)


# ── Вспомогательные функции ─────────────────────────────────────────────────


@router.message(F.text == "🔙 Назад")
async def back_handler(
    message: Message,
) -> None:
    """Возврат в главное меню."""
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu(),
    )


async def _cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(CANCEL, reply_markup=get_main_menu())


def _build_score_bar(score: int) -> str:
    """Строит визуальный прогресс-бар скора."""
    filled = round(score / 10)
    empty = 10 - filled
    return f"{'🟩' * filled}{'⬜' * empty}"

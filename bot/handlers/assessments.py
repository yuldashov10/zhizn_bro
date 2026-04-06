import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.client.api import APIError, BROApiClient
from bot.keyboards.inline import (
    get_answer_keyboard,
    get_attachment_result_keyboard,
    get_attachment_type_keyboard,
    get_tests_inline,
)
from bot.keyboards.reply import get_main_menu
from bot.messages.ru import (
    ERROR_GENERAL,
    TEST_CHOOSE,
    TEST_CHOOSE_MANUAL,
    TEST_CONFIRM_RESULT,
    TEST_QUESTION,
)
from bot.states.fsm import AssessmentStates

logger = logging.getLogger("bot")
router = Router()


@router.message(F.text == "🧪 Тест привязанности")
async def assessment_start(
    message: Message,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Показывает список доступных тестов."""
    logger.debug(f"Тест привязанности нажат: {message.from_user.id}")
    try:
        tests = await api.get_tests()
        if not tests:
            await message.answer("Тесты временно недоступны.")
            return
        await state.set_state(AssessmentStates.choosing_test)
        await message.answer(
            TEST_CHOOSE,
            reply_markup=get_tests_inline(tests),
        )
    except APIError:
        await message.answer(ERROR_GENERAL)


@router.callback_query(
    AssessmentStates.choosing_test,
    F.data.startswith("test:"),
)
async def test_selected(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Начинает выбранный тест."""
    test_id = int(callback.data.split(":")[1])
    try:
        session = await api.start_test(test_id)
        test = await api.get_test(test_id)
        questions = test.get("questions", [])

        await state.update_data(
            session_id=session["id"],
            questions=questions,
            current_question=0,
        )
        await state.set_state(AssessmentStates.answering)
        await _show_question(callback.message, state)
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
    finally:
        await callback.answer()


@router.callback_query(
    AssessmentStates.answering,
    F.data.startswith("answer:"),
)
async def answer_handler(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    answer = int(callback.data.split(":")[1])
    data = await state.get_data()
    question = data["questions"][data["current_question"]]

    try:
        session = await api.answer_question(
            session_id=data["session_id"],
            question_id=question["id"],
            answer=answer,
        )
        next_index = data["current_question"] + 1
        await state.update_data(current_question=next_index)

        if session.get("is_completed"):
            result = session.get("result_type", "secure")
            result_display = session.get("result_type_display", "Надёжный")

            await state.update_data(attachment_result=result)
            await state.set_state(AssessmentStates.confirming_result)

            await callback.message.answer(
                TEST_CONFIRM_RESULT.format(result=result_display),
                reply_markup=get_attachment_result_keyboard(result),
                parse_mode="HTML",
            )
        else:
            await _show_question(callback.message, state)

    except APIError:
        await callback.message.answer(ERROR_GENERAL)
    finally:
        await callback.answer()


async def _show_question(
    message: Message,
    state: FSMContext,
) -> None:
    """Показывает текущий вопрос теста."""
    data = await state.get_data()
    index = data["current_question"]
    questions = data["questions"]
    question = questions[index]

    await message.answer(
        TEST_QUESTION.format(
            current=index + 1,
            total=len(questions),
            text=question["text"],
        ),
        reply_markup=get_answer_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(
    AssessmentStates.confirming_result,
    F.data.startswith("attachment:confirm:"),
)
async def attachment_confirm_handler(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Пользователь согласен с результатом теста."""
    result = callback.data.split(":")[2]
    try:
        await api.update_me(
            attachment_type=result,
            attachment_source="bot_test",
        )
        await state.clear()
        await callback.message.answer(
            f"✅ Тип привязанности <b>{_get_display(result)}</b> сохранён!",
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
    finally:
        await callback.answer()


@router.callback_query(
    AssessmentStates.confirming_result,
    F.data == "attachment:manual",
)
async def attachment_manual_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Пользователь хочет выбрать тип вручную."""
    await callback.message.answer(
        TEST_CHOOSE_MANUAL,
        reply_markup=get_attachment_type_keyboard(),
    )
    await callback.answer()


def _get_display(attachment_type: str) -> str:
    """Возвращает читаемое название типа привязанности."""
    types = {
        "secure": "Надёжный",
        "anxious": "Тревожный",
        "avoidant": "Избегающий",
        "disorganized": "Дезорганизованный",
    }
    return types.get(attachment_type, attachment_type)


@router.callback_query(F.data.startswith("attachment:set:"))
async def attachment_set_handler(
    callback: CallbackQuery,
    state: FSMContext,
    api: BROApiClient,
) -> None:
    """Пользователь выбрал тип привязанности вручную."""
    result = callback.data.split(":")[2]
    try:
        await api.update_me(
            attachment_type=result,
            attachment_source="user_defined",
        )
        await state.clear()
        await callback.message.answer(
            f"✅ Тип привязанности <b>{_get_display(result)}</b> сохранён!",
            reply_markup=get_main_menu(),
            parse_mode="HTML",
        )
    except APIError:
        await callback.message.answer(ERROR_GENERAL)
    finally:
        await callback.answer()

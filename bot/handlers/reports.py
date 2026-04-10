import asyncio
import logging

import httpx
from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from decouple import config

from bot.client.api import APIError, BROApiClient
from bot.keyboards.inline import (
    get_candidates_for_report_inline,
    get_report_type_keyboard,
)
from bot.keyboards.reply import get_main_menu
from bot.messages.ru import (
    ERROR_GENERAL,
    REPORT_CHOOSE_CANDIDATE,
    REPORT_GENERATING,
)

logger = logging.getLogger("bot")
router = Router()


@router.message(F.text == "📊 Отчёты")
async def reports_menu_handler(
    message: Message,
    api: BROApiClient,
) -> None:
    """Показывает список кандидатов для выбора отчёта."""
    try:
        candidates = await api.get_candidates(is_active=True)
        if not candidates:
            await message.answer(
                "У тебя нет активных кандидатов.",
                reply_markup=get_main_menu(),
            )
            return
        await message.answer(
            REPORT_CHOOSE_CANDIDATE,
            reply_markup=get_candidates_for_report_inline(candidates),
        )
    except APIError:
        await message.answer(ERROR_GENERAL)


@router.callback_query(F.data.startswith("report_candidate:"))
async def report_candidate_selected(
    callback: CallbackQuery,
) -> None:
    """Показывает форматы отчётов для выбранного кандидата."""
    candidate_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        reply_markup=get_report_type_keyboard(candidate_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("report:"))
async def report_type_selected(  # noqa: skip
    callback: CallbackQuery,
    api: BROApiClient,
) -> None:
    parts = callback.data.split(":")
    report_type = parts[1]
    candidate_id = int(parts[2])

    try:
        candidate = await api.get_candidate(candidate_id)
        candidate_name = candidate["name"]
    except APIError:
        await callback.answer("Кандидат не найден")
        return

    generating_msg = await callback.message.answer(REPORT_GENERATING)

    photo_bytes = None
    telegram_photo_id = candidate.get("telegram_photo_id")
    if telegram_photo_id and report_type in ("png", "pdf"):
        photo_bytes = await api.get_telegram_photo(
            bot=callback.bot,
            file_id=telegram_photo_id,
        )

    try:
        response = await api.generate_report(
            report_type=report_type,
            candidate_id=candidate_id,
            photo_bytes=photo_bytes,
        )
        await generating_msg.delete()

        # Текстовый отчёт — отправляем фото + текст
        if report_type == "text":
            text = response.get("text", "")
            telegram_photo_id = candidate.get("telegram_photo_id")

            if telegram_photo_id:
                # Отправляем фото с текстом как подпись
                try:
                    await callback.message.answer_photo(
                        photo=telegram_photo_id,
                        caption=text,
                        parse_mode="HTML",
                    )
                except Exception:
                    # Если фото недоступно — просто текст
                    await callback.message.answer(text, parse_mode="HTML")
            else:
                await callback.message.answer(text, parse_mode="HTML")

            await callback.answer()
            return

        # Файловые отчёты
        report_id = response.get("id")
        file_url = None

        for _ in range(5):
            await asyncio.sleep(2)
            updated = await api.get_report(report_id)
            file_url = updated.get("file")
            if file_url:
                break

        if file_url:
            await _send_report_file(
                callback=callback,
                file_url=file_url,
                report_type=report_type,
                candidate_name=candidate_name,
                api=api,
            )
        else:
            await callback.message.answer(
                "⏳ Отчёт генерируется. Попробуй через минуту.",
            )

    except APIError as e:
        await generating_msg.delete()
        logger.error(f"Ошибка генерации отчёта: {e}")
        if "400" in str(e):
            await callback.message.answer(
                "❌ У кандидата нет событий.\n"
                "Сначала добавь хотя бы одно событие.",
                reply_markup=get_main_menu(),
            )
        else:
            await callback.message.answer(
                ERROR_GENERAL, reply_markup=get_main_menu()
            )
    finally:
        await callback.answer()


async def _send_report_file(
    callback: CallbackQuery,
    file_url: str,
    report_type: str,
    candidate_name: str,
    api: BROApiClient,
) -> None:
    """Скачивает и отправляет файл отчёта."""
    base_url = config("API_BASE_URL", default="http://localhost:8000")
    full_url = (
        f"{base_url}{file_url}" if file_url.startswith("/") else file_url
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            full_url,
            headers={"Authorization": f"Token {api._token}"},
        )
        if response.status_code != 200:
            await callback.message.answer(ERROR_GENERAL)
            return
        content = response.content

    safe_name = candidate_name.replace(" ", "_")
    extensions = {"pdf": "pdf", "excel": "xlsx", "png": "png"}
    ext = extensions.get(report_type, "bin")
    filename = f"report_{safe_name}.{ext}"
    file = BufferedInputFile(content, filename=filename)

    captions = {
        "pdf": f"📄 PDF отчёт: {candidate_name}",
        "excel": f"📊 Excel отчёт: {candidate_name}",
        "png": f"🖼 PNG дашборд: {candidate_name}",
    }
    caption = captions.get(report_type, "Отчёт готов")

    if report_type == "png":
        await callback.message.answer_photo(file, caption=caption)
    else:
        await callback.message.answer_document(file, caption=caption)

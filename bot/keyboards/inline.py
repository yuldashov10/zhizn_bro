from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_candidates_inline(candidates: list[dict]) -> InlineKeyboardMarkup:
    """Inline клавиатура со списком кандидатов."""
    builder = InlineKeyboardBuilder()
    for candidate in candidates:
        builder.row(
            InlineKeyboardButton(
                text=f"👤 {candidate['name']}",
                callback_data=f"candidate:{candidate['id']}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel",
        )
    )
    return builder.as_markup()


def get_candidate_actions(candidate_id: int) -> InlineKeyboardMarkup:
    """Действия с конкретным кандидатом."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 Добавить событие",
            callback_data=f"event:add:{candidate_id}",
        ),
        InlineKeyboardButton(
            text="📊 Скор",
            callback_data=f"candidate:score:{candidate_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 Сменить статус",
            callback_data=f"candidate:status:{candidate_id}",
        ),
        InlineKeyboardButton(
            text="📋 История",
            callback_data=f"candidate:history:{candidate_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🗃 Архивировать",
            callback_data=f"candidate:archive:{candidate_id}",
        )
    )
    return builder.as_markup()


def get_score_confirm(
    event_id: int,
    criterion_id: int,
    ai_score: int,
) -> InlineKeyboardMarkup:
    """Подтверждение оценки ИИ."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"✅ Согласен ({ai_score:+d})",
            callback_data=(
                f"score:confirm:{event_id}:{criterion_id}:{ai_score}"
            ),
        )
    )
    for score in [-2, -1, 0, 1, 2]:
        if score != ai_score:
            builder.add(
                InlineKeyboardButton(
                    text=f"{score:+d}",
                    callback_data=(
                        f"score:set:{event_id}:{criterion_id}:{score}"
                    ),
                )
            )
    builder.adjust(1, 5)
    return builder.as_markup()


def get_status_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора статуса кандидата."""
    statuses = [
        ("🤝 Знакомство", "meeting"),
        ("💑 Встречаемся", "dating"),
        ("❤️ Серьёзно", "serious"),
        ("⏸ Пауза", "pause"),
        ("🚫 Завершено", "ended"),
    ]
    builder = InlineKeyboardBuilder()
    for label, value in statuses:
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"status:{value}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel",
        )
    )
    return builder.as_markup()


def get_report_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа отчёта."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📄 PDF", callback_data="report:pdf"),
        InlineKeyboardButton(text="📊 Excel", callback_data="report:excel"),
        InlineKeyboardButton(text="🖼 PNG", callback_data="report:png"),
        InlineKeyboardButton(text="💬 Текст", callback_data="report:text"),
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel",
        )
    )
    return builder.as_markup()


def get_tests_inline(tests: list[dict]) -> InlineKeyboardMarkup:
    """Inline клавиатура со списком тестов привязанности."""
    builder = InlineKeyboardBuilder()
    for test in tests:
        validated = "✅" if test["is_validated"] else "📝"
        builder.row(
            InlineKeyboardButton(
                text=(
                    f"{validated} {test['name']} "
                    f"({test['questions_count']} вопросов)"
                ),
                callback_data=f"test:{test['id']}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel",
        )
    )
    return builder.as_markup()


def get_answer_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура ответов на вопросы теста (шкала Лайкерта 1-5)."""
    labels = [
        "1 - Совсем не согласен",
        "2 - Не согласен",
        "3 - Нейтрально",
        "4 - Согласен",
        "5 - Полностью согласен",
    ]
    builder = InlineKeyboardBuilder()
    for i, label in enumerate(labels, 1):
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"answer:{i}",
            )
        )
    return builder.as_markup()


def get_attachment_result_keyboard(result: str) -> InlineKeyboardMarkup:
    """Подтверждение или ручной выбор типа привязанности."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Согласен",
            callback_data=f"attachment:confirm:{result}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Указать свой вариант",
            callback_data="attachment:manual",
        )
    )
    return builder.as_markup()


def get_attachment_type_keyboard() -> InlineKeyboardMarkup:
    """Ручной выбор типа привязанности."""
    types = [
        ("🟢 Надёжный", "secure"),
        ("😰 Тревожный", "anxious"),
        ("🧊 Избегающий", "avoidant"),
        ("🌀 Дезорганизованный", "disorganized"),
    ]
    builder = InlineKeyboardBuilder()
    for label, value in types:
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"attachment:set:{value}",
            )
        )
    return builder.as_markup()

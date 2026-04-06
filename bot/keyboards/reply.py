from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Кандидаты"),
                KeyboardButton(text="📝 Добавить событие"),
            ],
            [
                KeyboardButton(text="📊 Отчёты"),
                KeyboardButton(text="🧪 Тест привязанности"),
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )


def get_candidates_menu() -> ReplyKeyboardMarkup:
    """Меню управления кандидатами."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить кандидата"),
                KeyboardButton(text="📋 Список кандидатов"),
            ],
            [
                KeyboardButton(text="🔙 Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой пропуска."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Пропустить")]],
        resize_keyboard=True,
    )


def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Подтвердить"),
                KeyboardButton(text="❌ Отмена"),
            ],
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Убирает клавиатуру."""
    return ReplyKeyboardRemove()

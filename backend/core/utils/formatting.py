from typing import Optional

PREVIEW_LEN: int = 60


class ScoreFormatter:
    """
    Утилита форматирования скора для отображения пользователю.

    Используется в текстовых отчётах и боте.
    """

    FILLED_BLOCK = "🟩"
    EMPTY_BLOCK = "⬜"
    MAX_SCORE = 100
    BAR_LENGTH = 10

    @classmethod
    def build_score_bar(cls, score: int | None) -> str:
        """
        Строит визуальный прогресс-бар скора.

        Args:
            score: скор от 0 до 100 или None если нет данных.

        Returns:
            str: строка из эмодзи, например "🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜."

        Example:
            >>> ScoreFormatter.build_score_bar(50)
            "🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜"
        """
        if score is None:
            return ""
        clamped = max(0, min(score, cls.MAX_SCORE))
        filled = round(clamped / cls.MAX_SCORE * cls.BAR_LENGTH)
        empty = cls.BAR_LENGTH - filled
        return f"{cls.FILLED_BLOCK * filled}{cls.EMPTY_BLOCK * empty}"

    @classmethod
    def score_display(cls, score: Optional[int]) -> str:
        """
        Форматирует скор для отображения.

        Args:
            score: скор от 0 до 100 или None.

        Returns:
            str: "78/100" или "Нет данных".
        """
        if score is None:
            return "Нет данных"
        return f"{score}/{cls.MAX_SCORE}"

    @classmethod
    def score_label(cls, score: Optional[int]) -> str:
        """
        Возвращает текстовую метку скора.

        Args:
            score: скор от 0 до 100 или None.

        Returns:
            str: "Отлично", "Хорошо", "Средне", "Плохо" или "—".
        """
        if score is None:
            return "—"
        if score >= 80:
            return "Отлично 🟢"
        elif score >= 60:
            return "Хорошо 🟡"
        elif score >= 40:
            return "Средне 🟠"
        else:
            return "Плохо 🔴"


def truncate(text: str | None, length: int = PREVIEW_LEN) -> str:
    """Усекает текст до заданной длины с добавлением многоточия."""
    if not text:
        return "—"
    return text[:length] + "..." if len(text) > length else text

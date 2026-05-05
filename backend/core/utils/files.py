import uuid
from datetime import datetime

from transliterate import translit
from transliterate.exceptions import LanguageDetectionError


class FileNameGenerator:
    """
    Генератор безопасных имён файлов.
    Транслитерирует кириллицу, добавляет дату и UUID.
    """

    DATE_FORMAT = "%d%m%Y%H%M%S"

    @classmethod
    def generate(
        cls,
        name: str,
        extension: str,
        uid_length: int = 8,
    ) -> str:
        """
        Генерирует безопасное имя файла.

        Args:
            name:       исходное имя (может содержать кириллицу)
            extension:  расширение файла без точки (pdf, xlsx, png)
            uid_length: длина UUID суффикса

        Returns:
            str: безопасное имя файла вида name_ddmmyyyyHHMMSS_uuid.ext

        Example:
            >>> FileNameGenerator.generate("Барби", "pdf")
            "barbi_07042026143022_a1b2c3d4.pdf"
        """
        safe_name = cls._transliterate(name)
        date_str = cls._date_string()
        uid = cls._uid(uid_length)
        ext = extension.lstrip(".")

        return f"{safe_name}_{date_str}_{uid}.{ext}"

    @classmethod
    def _transliterate(cls, name: str) -> str:
        """Транслитерирует кириллицу в латиницу и очищает строку."""
        try:
            latin = translit(name, "ru", reversed=True)
        except (LanguageDetectionError, Exception):
            latin = name

        # Оставляем только безопасные символы
        safe = "".join(
            c for c in latin if c.isalnum() or c in (" ", "_", "-")
        ).strip()

        # Заменяем пробелы и приводим к нижнему регистру
        safe = safe.replace(" ", "_").lower()

        # Если строка пустая — используем fallback
        return safe or "file"

    @classmethod
    def _date_string(cls) -> str:
        """Возвращает текущую дату и время в формате ddmmyyyyHHMMSS."""
        return datetime.now().strftime(cls.DATE_FORMAT)

    @classmethod
    def _uid(cls, length: int = 8) -> str:
        """Возвращает случайный UUID заданной длины."""
        return uuid.uuid4().hex[:length]

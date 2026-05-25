import uuid
from datetime import datetime, timezone

from slugify import slugify


class FileNameGenerator:
    """
    Генератор безопасных имён файлов.

    Транслитерирует название файла, добавляет дату и UUID.
    """

    _DATE_FORMAT: str = "%d%m%Y%H%M%S"

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
            name:       исходное имя (может содержать любой символ)
            extension:  расширение файла без точки (pdf, xlsx, png)
            uid_length: длина UUID суффикса (по умолчанию 8)

        Returns:
            str: безопасное имя файла вида name_ddmmyyyyHHMMSS_uuid.ext

        Example:
            >>> FileNameGenerator.generate("Барби", "pdf")
            "barbi_07042026143022_a1b2c3d4.pdf"
        """
        safe_name = cls._transliterate(name)
        date_str = cls._date_string()
        uid = cls._uid(uid_length)
        ext = extension.removeprefix(".")

        return f"{safe_name}_{date_str}_{uid}.{ext}"

    @classmethod
    def _transliterate(cls, name: str) -> str:
        """Транслитерирует название файла в латиницу."""
        return slugify(name, separator="_") or "file"

    @classmethod
    def _date_string(cls) -> str:
        """Возвращает текущую дату и время в формате ddmmyyyyHHMMSS."""
        return datetime.now(tz=timezone.utc).strftime(cls._DATE_FORMAT)

    @classmethod
    def _uid(cls, length: int = 8) -> str:
        """Возвращает случайный UUID заданной длины."""
        return uuid.uuid4().hex[:length]

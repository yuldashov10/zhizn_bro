import logging

from constance import config
from core.utils import ScoreFormatter

logger = logging.getLogger("apps.reports")


class TextReportBuilder:
    """
    Строитель текстового отчёта для отправки в Telegram.

    Формирует HTML-форматированный текст с основной информацией
    о кандидате, скором, событиями и watermark ботa.
    """

    MAX_EVENTS = 3
    MAX_TEXT_LEN = 60

    @classmethod
    def build(cls, candidate) -> str:
        """
        Генерирует полный текстовый отчёт по кандидату.

        Args:
            candidate: объект Candidate

        Returns:
            str: HTML-форматированный текст отчёта
        """
        from apps.events.services import ScoringService

        score = ScoringService.calculate(candidate)
        events_count = candidate.events.count()

        lines = []
        lines.extend(cls._build_header(candidate))
        lines.extend(cls._build_score_section(score, events_count))
        lines.extend(cls._build_hard_stop_section(candidate))
        lines.extend(cls._build_events_section(candidate))
        lines.append(cls._build_watermark())

        return "\n".join(lines)

    @classmethod
    def _build_header(cls, candidate) -> list[str]:
        """Формирует заголовок отчёта с основными данными кандидата."""
        return [
            f"📊 <b>Отчёт: {candidate.name}</b>\n",
            f"Возраст: {candidate.age or '—'}",
            f"Познакомились: {candidate.met_at or '—'}",
            f"Тип привязанности: "
            f"{candidate.get_ai_attachment_type_display() or '—'}",
            f"Событий: {candidate.events.count()}",
        ]

    @classmethod
    def _build_score_section(
        cls,
        score: int | None,
        events_count: int,
    ) -> list[str]:
        """Формирует секцию со скором, прогресс-баром и количеством событий."""
        if score is not None:
            return [
                f"\n{ScoreFormatter.build_score_bar(score)}",
                f"<b>Скор: {ScoreFormatter.score_display(score)}</b>"
                f" — {ScoreFormatter.score_label(score)}",
                f"<i>На основе {events_count} событий</i>",
            ]
        return ["\n<i>Недостаточно данных для скора</i>"]

    @classmethod
    def _build_hard_stop_section(cls, candidate) -> list[str]:
        """Формирует предупреждение если сработал Hard Stop."""
        if candidate.hard_stop_triggered:
            return ["\n🚨 <b>Hard Stop сработал!</b>"]
        return []

    @classmethod
    def _build_events_section(cls, candidate) -> list[str]:
        """Формирует секцию с последними событиями."""
        recent = candidate.events.order_by("-created_at")[: cls.MAX_EVENTS]
        if not recent:
            return []

        lines = ["\n<b>Последние события:</b>"]
        for event in recent:
            text = event.raw_text
            if len(text) > cls.MAX_TEXT_LEN:
                text = text[: cls.MAX_TEXT_LEN] + "..."
            lines.append(f"• {text}")
        return lines

    @classmethod
    def _get_bot_name(cls) -> str:
        """Возвращает название бота из настроек."""
        return config.BOT_NAME

    @classmethod
    def _get_watermark(cls) -> str:
        """Возвращает watermark из настроек."""
        return config.BOT_USERNAME

    @classmethod
    def _build_watermark(cls) -> str:
        """Формирует watermark."""
        return (
            f"\n<i>Сгенерировано <b>{cls._get_bot_name()}</b>"
            f" - {cls._get_watermark()}</i>"
        )

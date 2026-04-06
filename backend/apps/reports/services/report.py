import logging

from django.core.files.base import ContentFile

from apps.candidates.models import Candidate
from apps.reports.models import ReportLog
from apps.reports.services.excel import generate_excel
from apps.reports.services.pdf import generate_pdf
from apps.reports.services.png import generate_png

logger = logging.getLogger("apps.reports")


class ReportService:
    """
    Основной сервис генерации отчётов.
    Координирует генерацию и сохранение файлов.
    """

    @classmethod
    def generate(cls, report: ReportLog) -> ReportLog:
        """
        Генерирует отчёт и сохраняет файл.
        Обновляет ReportLog с путём к файлу.
        """
        if report.report_type == ReportLog.ReportType.TEXT:
            return report

        candidate = report.candidate
        if not candidate:
            logger.warning(f"Отчёт {report.pk} без кандидата — пропускаем")
            return report

        try:
            content, filename, content_type = cls._generate_file(
                report_type=report.report_type,
                candidate=candidate,
            )
            report.file.save(
                filename,
                ContentFile(content),
                save=True,
            )
            logger.info(f"Отчёт {report.pk} сгенерирован: {filename}")
        except Exception as e:
            logger.error(f"Ошибка генерации отчёта {report.pk}: {e}")
            raise

        return report

    @classmethod
    def _generate_file(
        cls,
        report_type: str,
        candidate: Candidate,
    ) -> tuple[bytes, str, str]:
        """
        Генерирует файл нужного типа.
        Возвращает (содержимое, имя файла, content_type).
        """
        safe_name = (
            "".join(
                c for c in candidate.name if c.isalnum() or c in (" ", "_")
            )
            .strip()
            .replace(" ", "_")
        )

        generators = {
            ReportLog.ReportType.PDF: (
                generate_pdf,
                f"report_{safe_name}.pdf",
                "application/pdf",
            ),
            ReportLog.ReportType.EXCEL: (
                generate_excel,
                f"report_{safe_name}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # noqa: skip
            ),
            ReportLog.ReportType.PNG: (
                generate_png,
                f"report_{safe_name}.png",
                "image/png",
            ),
        }

        generator_fn, filename, content_type = generators[report_type]
        content = generator_fn(candidate)
        return content, filename, content_type

    @classmethod
    def generate_text_report(cls, candidate: Candidate) -> str:
        """
        Генерирует текстовый отчёт для отправки в Telegram.
        """
        from apps.events.services import ScoringService

        score = ScoringService.calculate(candidate)
        events_count = candidate.events.count()
        score_bar = cls._build_score_bar(score)

        lines = [
            f"📊 <b>Отчёт: {candidate.name}</b>\n",
            f"Возраст: {candidate.age or '—'}",
            f"Познакомились: {candidate.met_at or '—'}",
            f"Тип привязанности: "
            f"{candidate.get_ai_attachment_type_display() or '—'}",
            f"Событий: {events_count}",
        ]

        if score is not None:
            lines += [
                f"\n{score_bar}",
                f"<b>Скор: {score}/100</b>",
            ]
        else:
            lines.append("\n<i>Недостаточно данных для скора</i>")

        if candidate.hard_stop_triggered:
            lines.append("\n🚨 <b>Hard Stop сработал!</b>")

        # Последние 3 события
        recent_events = candidate.events.order_by("-created_at")[:3]
        if recent_events:
            lines.append("\n<b>Последние события:</b>")
            for event in recent_events:
                lines.append(f"• {event.raw_text[:60]}")

        lines.append("\n<i>Сгенерировано @zhizn_bro_bot</i>")
        return "\n".join(lines)

    @staticmethod
    def _build_score_bar(score: int | None) -> str:
        if score is None:
            return ""
        filled = round(score / 10)
        empty = 10 - filled
        return f"{'🟩' * filled}{'⬜' * empty}"

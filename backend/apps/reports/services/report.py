import logging

from django.core.files.base import ContentFile

from apps.candidates.models import Candidate
from apps.reports.models import ReportLog
from apps.reports.services.excel import generate_excel
from apps.reports.services.pdf import generate_pdf
from apps.reports.services.png import generate_png
from apps.reports.services.text_report import TextReportBuilder
from core.utils import FileNameGenerator

logger = logging.getLogger("apps.reports")


class ReportService:
    """
    Основной сервис генерации отчётов.
    Координирует генерацию и сохранение файлов.
    """

    @classmethod
    def generate(
        cls, report: ReportLog, photo_bytes: bytes | None = None
    ) -> ReportLog:
        """
        Генерирует отчёт и сохраняет файл.
        Обновляет ReportLog с путём к файлу.
        """
        if report.report_type == ReportLog.ReportType.TEXT:
            return report

        candidate = report.candidate
        if not candidate:
            return report

        try:
            content, filename, content_type = cls._generate_file(
                report_type=report.report_type,
                candidate=candidate,
                photo_bytes=photo_bytes,
            )
            report.file.save(filename, ContentFile(content), save=True)
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
        photo_bytes: bytes | None = None,
    ) -> tuple[bytes, str, str]:

        extensions = {
            ReportLog.ReportType.PDF: ("pdf", "application/pdf"),
            ReportLog.ReportType.EXCEL: (
                "xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # noqa: skip
            ),
            ReportLog.ReportType.PNG: ("png", "image/png"),
        }
        ext, content_type = extensions[report_type]
        filename = FileNameGenerator.generate(
            name=candidate.name,
            extension=ext,
        )

        generators = {
            ReportLog.ReportType.PDF: lambda c: generate_pdf(c, photo_bytes),
            ReportLog.ReportType.EXCEL: generate_excel,
            ReportLog.ReportType.PNG: lambda c: generate_png(c, photo_bytes),
        }
        content = generators[report_type](candidate)
        return content, filename, content_type

    @classmethod
    def generate_text_report(cls, candidate) -> str:
        """
        Генерирует текстовый отчёт через TextReportBuilder.

        Args:
            candidate: объект Candidate

        Returns:
            str: HTML-форматированный текст
        """
        return TextReportBuilder.build(candidate)

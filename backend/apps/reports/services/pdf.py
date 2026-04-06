import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from apps.candidates.models import Candidate
from apps.events.services import ScoringService
from apps.reports.services.fonts import (
    FONT_BOLD,
    FONT_BOLD_ITALIC,
    FONT_ITALIC,
    FONT_MONO,
    FONT_NORMAL,
)


def _register_fonts() -> bool:
    """
    Регистрирует шрифты DejaVu для поддержки кириллицы.
    Возвращает True если успешно.
    """
    try:
        pdfmetrics.registerFont(TTFont("DVSans", FONT_NORMAL))
        pdfmetrics.registerFont(TTFont("DVSans-Bold", FONT_BOLD))
        pdfmetrics.registerFont(TTFont("DVMono", FONT_MONO))
        pdfmetrics.registerFont(TTFont("DVSans-Italic", FONT_ITALIC))
        pdfmetrics.registerFont(TTFont("DVSans-BoldItalic", FONT_BOLD_ITALIC))
        registerFontFamily(
            "DVSans",
            normal="DVSans",
            bold="DVSans-Bold",
            italic="DVSans-Italic",
            boldItalic="DVSans-BoldItalic",
        )
        return True
    except Exception as e:
        import logging

        logging.getLogger("apps.reports").error(
            f"Ошибка регистрации шрифтов: {e}"
        )
        return False


_FONTS_REGISTERED = _register_fonts()

PURPLE = colors.HexColor("#534AB7")
TEAL = colors.HexColor("#0F6E56")
TEAL_L = colors.HexColor("#E1F5EE")
GRAY = colors.HexColor("#444441")
GRAY_L = colors.HexColor("#F1EFE8")
GRAY_M = colors.HexColor("#D3D1C7")
WHITE = colors.white
BLACK = colors.HexColor("#2C2C2A")
RED_L = colors.HexColor("#FCEBEB")
RED = colors.HexColor("#A32D2D")
GREEN_L = colors.HexColor("#EAF3DE")
GREEN = colors.HexColor("#3B6D11")

NORMAL = "DVSans"
BOLD = "DVSans-Bold"
MONO = "DVMono"


def _style(name: str, **kw) -> ParagraphStyle:
    return ParagraphStyle(name, **kw)


def _on_page(canvas, doc) -> None:
    """Верхний и нижний колонтитул."""
    W, H = A4
    canvas.saveState()
    canvas.setFillColor(PURPLE)
    canvas.rect(0, H - 8 * mm, W, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(BOLD, 8)
    canvas.drawString(20 * mm, H - 5.5 * mm, "Жизнь БРО — Отчёт")
    canvas.setFont(NORMAL, 8)
    canvas.drawRightString(W - 20 * mm, H - 5.5 * mm, "@zhizn_bro_bot")
    canvas.setStrokeColor(GRAY_M)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 14 * mm, W - 20 * mm, 14 * mm)
    canvas.setFillColor(GRAY_M)
    canvas.setFont(NORMAL, 8)
    canvas.drawString(20 * mm, 10 * mm, f"Страница {doc.page}")
    canvas.drawRightString(
        W - 20 * mm,
        10 * mm,
        f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
    )
    canvas.restoreState()


def generate_pdf(candidate: Candidate) -> bytes:  # noqa: skip
    """
    Генерирует PDF отчёт по кандидату.
    Возвращает байты PDF файла.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    W = 170 * mm
    story = []

    ST = {
        "title": _style(
            "title",
            fontName=BOLD,
            fontSize=20,
            textColor=BLACK,
            spaceAfter=4,
            leading=26,
        ),
        "subtitle": _style(
            "subtitle",
            fontName=NORMAL,
            fontSize=12,
            textColor=GRAY,
            spaceAfter=12,
            leading=16,
        ),
        "h1": _style(
            "h1",
            fontName=BOLD,
            fontSize=13,
            textColor=PURPLE,
            spaceBefore=14,
            spaceAfter=6,
            leading=18,
        ),
        "body": _style(
            "body",
            fontName=NORMAL,
            fontSize=10,
            textColor=GRAY,
            spaceAfter=4,
            leading=15,
        ),
        "table_h": _style(
            "table_h", fontName=BOLD, fontSize=9, textColor=WHITE, leading=13
        ),
        "table_l": _style(
            "table_l", fontName=NORMAL, fontSize=9, textColor=GRAY, leading=13
        ),
        "table_lb": _style(
            "table_lb", fontName=BOLD, fontSize=9, textColor=BLACK, leading=13
        ),
        "table_c": _style(
            "table_c", fontName=NORMAL, fontSize=9, textColor=GRAY, leading=13
        ),
    }

    def P(txt, st="body"):
        return Paragraph(txt, ST[st])

    def SP(h=6):
        return Spacer(1, h)

    def HR():
        return HRFlowable(
            width="100%",
            thickness=0.5,
            color=GRAY_M,
            spaceAfter=6,
            spaceBefore=6,
        )

    # ── Заголовок ────────────────────────────────────────────────────────
    story += [
        SP(4),
        P(f"Отчёт: {candidate.name}", "title"),
        P(
            f"Пользователь: @{candidate.user.username or candidate.user.telegram_id}",  # noqa: skip
            "subtitle",
        ),
        HR(),
    ]

    # ── Основная информация ───────────────────────────────────────────────
    story.append(P("Основная информация", "h1"))
    score = ScoringService.calculate(candidate)
    events_count = candidate.events.count()

    info_data = [
        [P("Имя", "table_lb"), P(candidate.name, "table_l")],
        [P("Возраст", "table_lb"), P(str(candidate.age or "—"), "table_l")],
        [
            P("Познакомились", "table_lb"),
            P(candidate.met_at or "—", "table_l"),
        ],
        [
            P("Тип привязанности", "table_lb"),
            P(candidate.get_ai_attachment_type_display() or "—", "table_l"),
        ],
        [P("Событий", "table_lb"), P(str(events_count), "table_l")],
        [
            P("Hard Stop", "table_lb"),
            P("Да" if candidate.hard_stop_triggered else "Нет", "table_l"),
        ],
        [
            P("Добавлен", "table_lb"),
            P(candidate.created_at.strftime("%d.%m.%Y"), "table_l"),
        ],
    ]
    t_info = Table(info_data, colWidths=[50 * mm, 120 * mm])
    t_info.setStyle(
        TableStyle(
            [
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [GRAY_L, WHITE]),
                ("BOX", (0, 0), (-1, -1), 0.5, GRAY_M),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, GRAY_M),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story += [t_info, SP(10)]

    # ── Скор ─────────────────────────────────────────────────────────────
    story.append(P("Итоговый скор", "h1"))
    if score is not None:
        score_color = (
            GREEN_L
            if score >= 80
            else (
                colors.HexColor("#FAEEDA")
                if score >= 60
                else colors.HexColor("#FCEBEB")
            )
        )
        score_data = [[P(f"Скор: {score} / 100", "table_lb")]]
        t_score = Table(score_data, colWidths=[W])
        t_score.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), score_color),
                    ("BOX", (0, 0), (-1, -1), 0.8, GRAY_M),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("LEFTPADDING", (0, 0), (-1, -1), 16),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story += [t_score, SP(10)]
    else:
        story += [P("Недостаточно данных для расчёта скора.", "body"), SP(10)]

    # ── История статусов ─────────────────────────────────────────────────
    status_history = candidate.status_history.all()
    if status_history.exists():
        story.append(P("История статусов", "h1"))
        status_rows = [
            [
                P("Статус", "table_h"),
                P("Дата", "table_h"),
                P("Примечание", "table_h"),
            ]
        ]
        for sh in status_history:
            status_rows.append(
                [
                    P(sh.get_status_display(), "table_lb"),
                    P(sh.started_at.strftime("%d.%m.%Y"), "table_l"),
                    P(
                        (
                            sh.note[:60] + "..."
                            if len(sh.note) > 60
                            else sh.note or "—"
                        ),
                        "table_l",
                    ),
                ]
            )
        t_status = Table(status_rows, colWidths=[40 * mm, 30 * mm, 100 * mm])
        t_status.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, TEAL_L]),
                    ("BOX", (0, 0), (-1, -1), 0.5, TEAL),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, GRAY_M),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story += [t_status, SP(10)]

    # ── События ──────────────────────────────────────────────────────────
    events = candidate.events.prefetch_related("scores__criterion").all()
    if events.exists():
        story.append(P("События", "h1"))
        event_rows = [
            [
                P("Событие", "table_h"),
                P("Критерий", "table_h"),
                P("Балл", "table_h"),
                P("Дата", "table_h"),
            ]
        ]
        for event in events:
            scores = event.scores.all()
            if scores:
                for i, score_obj in enumerate(scores):
                    event_rows.append(
                        [
                            P(
                                (
                                    event.raw_text[:50] + "..."
                                    if i == 0 and len(event.raw_text) > 50
                                    else ("" if i > 0 else event.raw_text)
                                ),
                                "table_l",
                            ),
                            P(score_obj.criterion.name, "table_lb"),
                            P(f"{score_obj.final_score:+d}", "table_l"),
                            P(
                                (
                                    event.created_at.strftime("%d.%m")
                                    if i == 0
                                    else ""
                                ),
                                "table_l",
                            ),
                        ]
                    )
            else:
                event_rows.append(
                    [
                        P(
                            (
                                event.raw_text[:50] + "..."
                                if len(event.raw_text) > 50
                                else event.raw_text
                            ),
                            "table_l",
                        ),
                        P("—", "table_l"),
                        P("—", "table_l"),
                        P(event.created_at.strftime("%d.%m"), "table_l"),
                    ]
                )

        t_events = Table(
            event_rows, colWidths=[70 * mm, 40 * mm, 20 * mm, 20 * mm]
        )
        t_events.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), GRAY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_L]),
                    ("BOX", (0, 0), (-1, -1), 0.5, GRAY_M),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, GRAY_M),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story += [t_events, SP(10)]

    # ── Watermark ─────────────────────────────────────────────────────────
    watermark_data = [
        [
            P(
                "Отчёт сгенерирован ботом @zhizn_bro_bot • Жизнь БРО (Без Розовых Очков)",  # noqa: skip
                "body",
            )
        ]
    ]
    t_wm = Table(watermark_data, colWidths=[W])
    t_wm.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GRAY_L),
                ("BOX", (0, 0), (-1, -1), 0.5, GRAY_M),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(t_wm)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buffer.getvalue()

import io
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from apps.candidates.models import Candidate
from apps.events.services import ScoringService
from apps.reports.services.fonts import FONT_BOLD, FONT_NORMAL


def _load_fonts():
    """Загружает шрифты с явными путями."""
    try:
        return {
            "title": ImageFont.truetype(FONT_BOLD, 24),
            "large": ImageFont.truetype(FONT_BOLD, 48),
            "body": ImageFont.truetype(FONT_NORMAL, 16),
            "small": ImageFont.truetype(FONT_NORMAL, 12),
            "medium": ImageFont.truetype(FONT_BOLD, 18),
        }
    except OSError as e:
        import logging

        logging.getLogger("apps.reports").error(f"Шрифты не найдены: {e}")
        default = ImageFont.load_default()
        return {
            k: default for k in ["title", "large", "body", "small", "medium"]
        }


def generate_png(candidate: Candidate) -> bytes:
    """
    Генерирует PNG дашборд по кандидату.
    Возвращает байты PNG файла.
    """
    W, H = 900, 580  # увеличиваем размер
    img = Image.new("RGB", (W, H), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    fonts = _load_fonts()
    font_title = fonts["title"]
    font_large = fonts["large"]
    font_body = fonts["body"]
    font_small = fonts["small"]
    font_medium = fonts["medium"]

    # Верхняя полоса
    draw.rectangle([0, 0, W, 60], fill="#534AB7")
    draw.text((20, 18), "Жизнь БРО", font=font_title, fill="#FFFFFF")
    draw.text((W - 220, 20), "@zhizn_bro_bot", font=font_body, fill="#EEEDFE")

    # Имя кандидата
    draw.text((20, 80), candidate.name, font=font_title, fill="#2C2C2A")

    info_lines = [
        f"Возраст: {candidate.age or '—'}",
        f"Познакомились: {candidate.met_at or '—'}",
        "Тип привязанности: "
        f"{candidate.get_ai_attachment_type_display() or '—'}",
        f"Событий: {candidate.events.count()}",
    ]
    y = 115
    for line in info_lines:
        draw.text((20, y), line, font=font_body, fill="#444441")
        y += 26

    # Скор — блок справа
    score = ScoringService.calculate(candidate)
    draw.rectangle(
        [W - 280, 70, W - 20, 260], fill="#F1EFE8", outline="#D3D1C7", width=1
    )

    score_text = str(score) if score is not None else "—"
    score_color = (
        "#3B6D11"
        if score and score >= 80
        else (
            "#854F0B"
            if score and score >= 60
            else "#A32D2D" if score else "#444441"
        )
    )
    draw.text((W - 220, 85), "Скор", font=font_medium, fill="#444441")
    draw.text((W - 230, 115), score_text, font=font_large, fill=score_color)
    draw.text((W - 195, 175), "из 100", font=font_body, fill="#888780")

    # Прогресс-бар
    if score is not None:
        bar_x, bar_y = W - 260, 210
        bar_w, bar_h = 220, 16
        draw.rectangle(
            [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill="#D3D1C7"
        )
        fill_w = int(bar_w * score / 100)
        fill_color = (
            "#3B6D11"
            if score >= 80
            else "#854F0B" if score >= 60 else "#A32D2D"
        )
        if fill_w > 0:
            draw.rectangle(
                [bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], fill=fill_color
            )

    # Hard Stop
    if candidate.hard_stop_triggered:
        draw.rectangle(
            [20, 270, W - 20, 310], fill="#FCEBEB", outline="#A32D2D", width=1
        )
        draw.text(
            (30, 283), "Hard Stop сработал!", font=font_medium, fill="#A32D2D"
        )
        events_y = 325
    else:
        events_y = 285

    # Разделитель
    draw.line(
        [20, events_y - 15, W - 20, events_y - 15], fill="#D3D1C7", width=1
    )

    # Последние события
    events = candidate.events.prefetch_related("scores__criterion").order_by(
        "-created_at"
    )[:4]
    if events:
        draw.text(
            (20, events_y),
            "Последние события:",
            font=font_medium,
            fill="#2C2C2A",
        )
        y = events_y + 28
        for event in events:
            scores = event.scores.all()
            score_str = (
                ", ".join(
                    f"{s.criterion.name}: {s.final_score:+d}" for s in scores
                )
                if scores
                else "—"
            )

            # Текст события
            raw = (
                event.raw_text[:55] + "..."
                if len(event.raw_text) > 55
                else event.raw_text
            )
            draw.text((20, y), f"• {raw}", font=font_small, fill="#2C2C2A")
            y += 18

            # Оценки на следующей строке
            if score_str != "—":
                draw.text(
                    (30, y), score_str[:90], font=font_small, fill="#888780"
                )
                y += 20
            else:
                y += 4

    # Нижняя полоса
    draw.rectangle([0, H - 36, W, H], fill="#F1EFE8")
    draw.text(
        (20, H - 24),
        "Сгенерировано: "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')} • @zhizn_bro_bot",
        font=font_small,
        fill="#888780",
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()

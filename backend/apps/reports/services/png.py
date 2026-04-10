import io
from datetime import datetime

from constance import config
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


def _make_circle_avatar(image_bytes: bytes, size: int = 80) -> Image.Image:
    """Создаёт круглый аватар из байтов изображения."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)

    # Создаём круглую маску
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)

    # Применяем маску
    result = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    result.paste(img, (0, 0), mask)
    return result


def generate_png(  # noqa: skip
    candidate: Candidate, photo_bytes: bytes | None = None
) -> bytes:
    """
    Генерирует PNG дашборд по кандидату.
    Возвращает байты PNG файла.
    """
    W, H = 900, 580
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
    draw.text((20, 18), config.BOT_NAME, font=font_title, fill="#FFFFFF")
    draw.text(
        (W - 220, 20), config.BOT_USERNAME, font=font_body, fill="#EEEDFE"
    )

    # Аватар если есть фото
    avatar_size = 80
    name_x = 20
    if photo_bytes:
        try:
            avatar = _make_circle_avatar(photo_bytes, avatar_size)
            # Конвертируем основное изображение в RGBA для вставки аватара
            img_rgba = img.convert("RGBA")
            img_rgba.paste(avatar, (20, 75), avatar)
            img = img_rgba.convert("RGB")
            draw = ImageDraw.Draw(img)
            name_x = avatar_size + 30  # сдвигаем имя вправо
        except Exception:
            pass

    # Имя кандидата
    draw.text((name_x, 80), candidate.name, font=font_title, fill="#2C2C2A")

    info_y = 115 if not photo_bytes else 170
    info_lines = [
        f"Возраст: {candidate.age or '—'}",
        f"Познакомились: {candidate.met_at or '—'}",
        "Тип привязанности: "
        f"{candidate.get_ai_attachment_type_display() or '—'}",
        f"Событий: {candidate.events.count()}",
    ]
    y = info_y
    for line in info_lines:
        draw.text((20, y), line, font=font_body, fill="#444441")
        y += 26

    # Скор блок
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

    if candidate.hard_stop_triggered:
        draw.rectangle(
            [20, 270, W - 20, 310], fill="#FCEBEB", outline="#A32D2D", width=1
        )
        draw.text(
            (30, 283), "Hard Stop сработал!", font=font_medium, fill="#A32D2D"
        )
        events_y = 325
    else:
        events_y = y + 20

    draw.line(
        [20, events_y - 10, W - 20, events_y - 10], fill="#D3D1C7", width=1
    )

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
            raw = (
                event.raw_text[:55] + "..."
                if len(event.raw_text) > 55
                else event.raw_text
            )
            draw.text((20, y), f"• {raw}", font=font_small, fill="#2C2C2A")
            y += 18
            if score_str != "—":
                draw.text(
                    (30, y), score_str[:90], font=font_small, fill="#888780"
                )
                y += 20
            else:
                y += 4

    draw.rectangle([0, H - 36, W, H], fill="#F1EFE8")
    draw.text(
        (20, H - 24),
        "Сгенерировано: "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')} "
        f"• {config.BOT_USERNAME}",
        font=font_small,
        fill="#888780",
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()

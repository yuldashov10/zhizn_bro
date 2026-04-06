import io
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from apps.candidates.models import Candidate
from apps.events.services import ScoringService


def generate_png(candidate: Candidate) -> bytes:
    """
    Генерирует PNG дашборд по кандидату.
    Возвращает байты PNG файла.
    """
    W, H = 800, 500
    img = Image.new("RGB", (W, H), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_title = ImageFont.truetype(font_bold_path, 24)
        font_large = ImageFont.truetype(font_bold_path, 48)
        font_body = ImageFont.truetype(font_path, 16)
        font_small = ImageFont.truetype(font_path, 12)
        font_medium = ImageFont.truetype(font_bold_path, 18)
    except OSError:
        font_title = ImageFont.load_default()
        font_large = font_title
        font_body = font_title
        font_small = font_title
        font_medium = font_title

    # Верхняя полоса
    draw.rectangle([0, 0, W, 60], fill="#534AB7")
    draw.text((20, 18), "Жизнь БРО", font=font_title, fill="#FFFFFF")
    draw.text((W - 200, 20), "@zhizn_bro_bot", font=font_body, fill="#EEEDFE")

    # Имя кандидата
    draw.text((20, 80), candidate.name, font=font_title, fill="#2C2C2A")

    info_lines = [
        f"Возраст: {candidate.age or '—'}",
        f"Познакомились: {candidate.met_at or '—'}",
        f"Тип привязанности: "
        f"{candidate.get_ai_attachment_type_display() or '—'}",
        f"Событий: {candidate.events.count()}",
    ]
    y = 115
    for line in info_lines:
        draw.text((20, y), line, font=font_body, fill="#444441")
        y += 28

    # Скор
    score = ScoringService.calculate(candidate)
    draw.rectangle(
        [W - 260, 70, W - 20, 250], fill="#F1EFE8", outline="#D3D1C7", width=1
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
    draw.text((W - 200, 90), "Скор", font=font_medium, fill="#444441")
    draw.text((W - 215, 120), score_text, font=font_large, fill=score_color)
    draw.text((W - 180, 175), "из 100", font=font_body, fill="#888780")

    # Прогресс-бар скора
    if score is not None:
        bar_x, bar_y = W - 240, 210
        bar_w, bar_h = 200, 16
        draw.rectangle(
            [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
            fill="#D3D1C7",
            outline="#D3D1C7",
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

    # Hard Stop предупреждение
    if candidate.hard_stop_triggered:
        draw.rectangle(
            [20, 265, W - 20, 305], fill="#FCEBEB", outline="#A32D2D", width=1
        )
        draw.text(
            (30, 278),
            "⚠ Hard Stop сработал!",
            font=font_medium,
            fill="#A32D2D",
        )

    # Последние события
    events = candidate.events.order_by("-created_at")[:5]
    if events:
        draw.text(
            (20, 320), "Последние события:", font=font_medium, fill="#2C2C2A"
        )
        y = 348
        for event in events:
            scores = event.scores.all()
            score_str = (
                ", ".join(
                    f"{s.criterion.name}: {s.final_score:+d}" for s in scores
                )
                if scores
                else "—"
            )
            text = f"• {event.raw_text[:45]}... [{score_str}]"
            draw.text((20, y), text, font=font_small, fill="#444441")
            y += 22

    # Нижняя полоса (watermark)
    draw.rectangle([0, H - 36, W, H], fill="#F1EFE8")
    draw.text(
        (20, H - 24),
        f"Сгенерировано: "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')} • @zhizn_bro_bot",
        font=font_small,
        fill="#888780",
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()

import platform
from pathlib import Path


def get_font_dir() -> Path:
    """Возвращает путь к шрифтам DejaVu в зависимости от ОС."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Fonts"
    else:  # Linux (продакшн, Docker)
        return Path("/usr/share/fonts/truetype/dejavu")


FONT_DIR = get_font_dir()

FONT_NORMAL = str(FONT_DIR / "DejaVuSans.ttf")
FONT_BOLD = str(FONT_DIR / "DejaVuSans-Bold.ttf")
FONT_MONO = str(FONT_DIR / "DejaVuSansMono.ttf")
FONT_ITALIC = str(FONT_DIR / "DejaVuSans-Oblique.ttf")
FONT_BOLD_ITALIC = str(FONT_DIR / "DejaVuSans-BoldOblique.ttf")

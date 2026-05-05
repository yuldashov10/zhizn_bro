import asyncio
import logging
import os
import sys
from pathlib import Path

# ── Пути должны быть настроены ДО любых импортов проекта ─────────────────
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

# ── Django должен быть настроен ДО импортов Django модулей ───────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django

django.setup()

# ── После django.setup() можно импортировать всё остальное ────────────────
import sentry_sdk
from decouple import config as env_config

from bot.main import main  # ← теперь core виден

sentry_dsn = env_config("SENTRY_DSN", default="")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=env_config("ENVIRONMENT", default="development"),
        release=env_config("APP_VERSION", default="1.0.0"),
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "bot": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
            "aiogram": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
)


if __name__ == "__main__":
    asyncio.run(main())

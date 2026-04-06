import asyncio
import logging
import logging.config
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

logging.config.dictConfig({
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
            "class":     "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "bot": {
            "handlers":  ["console"],
            "level":     "DEBUG",
            "propagate": False,
        },
        "aiogram": {
            "handlers":  ["console"],
            "level":     "INFO",
            "propagate": False,
        },
    },
})

import asyncio
from bot.main import main

if __name__ == "__main__":
    asyncio.run(main())

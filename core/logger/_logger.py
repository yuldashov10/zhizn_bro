import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from colorama import Fore, Style, init


from ._constants import LOG_FILE_BACKUP_COUNT, LOG_FILE_MAX_BYTES, LOG_LEVEL

init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG:    Fore.CYAN,
        logging.INFO:     Fore.GREEN,
        logging.WARNING:  Fore.YELLOW,
        logging.ERROR:    Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, Fore.WHITE)
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"


class ProjectLogger:
    _loggers: dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(
        cls,
        name: str = "app",
        log_file: str = "logs/app.log",
    ) -> logging.Logger:
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)

        logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.DEBUG))
        logger.handlers.clear()

        log_path = cls._create_logs_dir(log_file)
        logger.addHandler(cls._get_file_handler(log_path))
        cls._set_colored_stream_handler(logger)

        cls._loggers[name] = logger
        return logger

    @staticmethod
    def _get_file_handler(log_path: Path) -> RotatingFileHandler:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=LOG_FILE_MAX_BYTES,
            backupCount=LOG_FILE_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        return handler

    @staticmethod
    def _set_colored_stream_handler(logger: logging.Logger) -> None:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        ))
        logger.addHandler(handler)

    @staticmethod
    def _create_logs_dir(file: str) -> Path:
        log_path = Path(file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path

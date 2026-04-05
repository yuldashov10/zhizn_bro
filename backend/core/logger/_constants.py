from decouple import config

LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
LOG_FILE_BACKUP_COUNT: int = 5

LOG_LEVEL = config("LOG_LEVEL", default="DEBUG")

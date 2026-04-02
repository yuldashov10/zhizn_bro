class BROBaseException(Exception):
    """Базовое исключение проекта Жизнь БРО."""
    pass


class ValidationError(BROBaseException):
    """Ошибка валидации входных данных."""
    pass


class ProviderError(BROBaseException):
    """Ошибка AI провайдера."""
    pass

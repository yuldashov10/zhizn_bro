from rest_framework.throttling import UserRateThrottle


class AIRateThrottle(UserRateThrottle):
    """
    Кастомный троттлинг для эндпоинтов с AI анализом.
    Ограничивает количество запросов к AI провайдеру.
    """

    scope = "ai"

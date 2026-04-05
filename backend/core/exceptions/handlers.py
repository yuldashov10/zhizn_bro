from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context) -> Response | None:
    """
    Кастомный обработчик ошибок DRF.
    Приводит все ошибки к единому формату:
    {
        "error": "краткое описание",
        "detail": "подробное описание"
    }
    """
    response = exception_handler(exc, context)

    if response is None:
        return None

    error_map = {
        status.HTTP_400_BAD_REQUEST: "неверный запрос",
        status.HTTP_401_UNAUTHORIZED: "необходима авторизация",
        status.HTTP_403_FORBIDDEN: "доступ запрещён",
        status.HTTP_404_NOT_FOUND: "не найдено",
        status.HTTP_405_METHOD_NOT_ALLOWED: "метод не разрешён",
        status.HTTP_429_TOO_MANY_REQUESTS: "слишком много запросов",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "внутренняя ошибка сервера",
    }

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        detail = detail["detail"]
    elif isinstance(detail, list) and len(detail) == 1:
        detail = detail[0]

    response.data = {
        "error": error_map.get(response.status_code, "ошибка"),
        "detail": str(detail),
    }

    return response

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ExceptionResponseBuilder:
    """
    Строит унифицированный payload ошибки для DRF-ответа.

    Формат вывода:
        {
            "error": "краткое описание",
            "detail": "подробное описание"
        }
    """

    _STATUS_MESSAGES: dict[int, str] = {
        status.HTTP_400_BAD_REQUEST: "неверный запрос",
        status.HTTP_401_UNAUTHORIZED: "необходима авторизация",
        status.HTTP_403_FORBIDDEN: "доступ запрещён",
        status.HTTP_404_NOT_FOUND: "не найдено",
        status.HTTP_405_METHOD_NOT_ALLOWED: "метод не разрешён",
        status.HTTP_429_TOO_MANY_REQUESTS: "слишком много запросов",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "внутренняя ошибка сервера",
    }
    _FALLBACK_MESSAGE: str = "ошибка"

    def __init__(self, response: Response) -> None:
        self._response = response

    def build(self) -> dict[str, str]:
        """Возвращает итоговый payload для response.data."""
        return {
            "error": self._resolve_error_label(),
            "detail": self._resolve_detail(),
        }

    def _resolve_error_label(self) -> str:
        return self._STATUS_MESSAGES.get(
            self._response.status_code, self._FALLBACK_MESSAGE
        )

    def _resolve_detail(self) -> str:
        detail = self._response.data

        if isinstance(detail, dict) and "detail" in detail:
            return str(detail["detail"])

        if isinstance(detail, list) and len(detail) == 1:
            return str(detail[0])

        return str(detail)


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Кастомный обработчик ошибок DRF.

    Делегирует форматирование ответа классу ExceptionResponseBuilder.
    """
    response = exception_handler(exc, context)

    if response is None:
        return None

    response.data = ExceptionResponseBuilder(response).build()
    return response

import logging

import httpx
from core.exceptions.base import BROBaseException
from decouple import config

logger = logging.getLogger("bot")


class APIError(BROBaseException):
    """Ошибка запроса к API."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")


class BROApiClient:
    """
    HTTP клиент для взаимодействия с Django REST API.
    Все запросы бота к бэкенду идут через этот класс.
    """

    def __init__(self, token: str | None = None) -> None:
        base_url = config("API_BASE_URL", default="http://localhost:8000")
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=f"{base_url}/api/v1/",
            headers=self._build_headers(),
            timeout=30.0,
        )

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Token {self._token}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        """Базовый метод для всех запросов."""
        try:
            response = await self._client.request(method, endpoint, **kwargs)

            if response.status_code == 204:
                return {}

            data = response.json()

            if response.status_code >= 400:
                raise APIError(
                    status_code=response.status_code,
                    detail=data.get("detail", "Неизвестная ошибка"),
                )

            return data

        except httpx.TimeoutException:
            logger.error(f"Таймаут запроса: {method} {endpoint}")
            raise APIError(status_code=408, detail="Сервис не отвечает")
        except httpx.NetworkError as e:
            logger.error(f"Ошибка сети: {e}")
            raise APIError(status_code=503, detail="Сервис недоступен")

    async def close(self) -> None:
        """Закрывает HTTP соединение."""
        await self._client.aclose()

    # ── Auth ──────────────────────────────────────────────────────────────

    async def auth_telegram(
        self,
        telegram_id: int,
        username: str | None = None,
    ) -> dict:
        """Аутентификация через Telegram ID."""
        return await self._request(
            "POST",
            "auth/telegram/",
            json={
                "telegram_id": telegram_id,
                "username": username,
            },
        )

    # ── Users ─────────────────────────────────────────────────────────────

    async def get_me(self) -> dict:
        """Получить профиль текущего пользователя."""
        return await self._request("GET", "users/me/")

    async def update_me(self, **kwargs) -> dict:
        """Обновить профиль пользователя."""
        return await self._request("PATCH", "users/me/", json=kwargs)

    async def get_token_limit(self) -> dict:
        """Получить лимиты токенов."""
        return await self._request("GET", "users/me/token-limit/")

    # ── Assessments ───────────────────────────────────────────────────────

    async def get_tests(self) -> list[dict]:
        """Получить список тестов привязанности."""
        data = await self._request("GET", "assessments/tests/")
        if isinstance(data, list):
            return data
        return data.get("results", [])

    async def get_test(self, test_id: int) -> dict:
        """Получить детали теста."""
        return await self._request("GET", f"assessments/tests/{test_id}/")

    async def start_test(self, test_id: int) -> dict:
        """Начать прохождение теста."""
        return await self._request(
            "POST",
            f"assessments/tests/{test_id}/start/",
        )

    async def answer_question(
        self,
        session_id: int,
        question_id: int,
        answer: int,
    ) -> dict:
        """Ответить на вопрос теста."""
        return await self._request(
            "POST",
            f"assessments/sessions/{session_id}/answer/",
            json={
                "question": question_id,
                "answer": answer,
            },
        )

    async def get_session_result(self, session_id: int) -> dict:
        """Получить результат теста."""
        return await self._request(
            "GET",
            f"assessments/sessions/{session_id}/result/",
        )

    # ── Candidates ────────────────────────────────────────────────────────

    async def get_candidates(self, **filters) -> list[dict]:
        """Получить список кандидатов."""
        data = await self._request(
            "GET",
            "candidates/",
            params=filters,
        )
        return data.get("results", data)

    async def get_candidate(self, candidate_id: int) -> dict:
        """Получить детали кандидата."""
        return await self._request("GET", f"candidates/{candidate_id}/")

    async def create_candidate(self, **kwargs) -> dict:
        """Создать кандидата."""
        return await self._request("POST", "candidates/", json=kwargs)

    async def update_candidate(self, candidate_id: int, **kwargs) -> dict:
        """Обновить данные кандидата."""
        return await self._request(
            "PATCH",
            f"candidates/{candidate_id}/",
            json=kwargs,
        )

    async def archive_candidate(self, candidate_id: int) -> dict:
        """Архивировать кандидата."""
        return await self._request(
            "POST",
            f"candidates/{candidate_id}/archive/",
        )

    async def get_candidate_score(self, candidate_id: int) -> dict:
        """Получить скор кандидата."""
        return await self._request(
            "GET",
            f"candidates/{candidate_id}/score/",
        )

    async def get_status_history(self, candidate_id: int) -> dict:
        """Получить историю статусов кандидата."""
        return await self._request(
            "GET",
            f"candidates/{candidate_id}/status-history/",
        )

    async def update_status(
        self,
        candidate_id: int,
        status: str,
        note: str = "",
    ) -> dict:
        """Сменить статус кандидата."""
        return await self._request(
            "POST",
            f"candidates/{candidate_id}/status/",
            json={
                "status": status,
                "note": note,
            },
        )

    # ── Events ────────────────────────────────────────────────────────────

    async def get_events(self, candidate_id: int, **filters) -> list[dict]:
        """Получить события кандидата."""
        data = await self._request(
            "GET",
            "events/",
            params={"candidate": candidate_id, **filters},
        )
        return data.get("results", data)

    async def create_event(
        self,
        candidate_id: int,
        raw_text: str,
    ) -> dict:
        """Зафиксировать событие."""
        return await self._request(
            "POST",
            "events/",
            json={
                "candidate": candidate_id,
                "raw_text": raw_text,
            },
        )

    async def confirm_score(
        self,
        event_id: int,
        criterion_id: int,
        user_score: int | None = None,
        is_confirmed: bool = True,
    ) -> dict:
        """Подтвердить или скорректировать оценку ИИ."""
        return await self._request(
            "PATCH",
            f"events/{event_id}/confirm/",
            json={
                "criterion": criterion_id,
                "user_score": user_score,
                "is_confirmed": is_confirmed,
            },
        )

    # ── Hard Stops ────────────────────────────────────────────────────────

    async def get_hard_stops(self) -> list[dict]:
        """Получить список Hard Stops."""
        data = await self._request("GET", "hard-stops/")
        return data.get("results", data)

    # ── Criteria ──────────────────────────────────────────────────────────

    async def get_criteria(self) -> list[dict]:
        """Получить список критериев."""
        data = await self._request("GET", "criteria/")
        return data.get("results", data)

    # ── Reports ───────────────────────────────────────────────────────────

    async def get_reports(self, **filters) -> list[dict]:
        """Получить историю отчётов."""
        data = await self._request("GET", "reports/", params=filters)
        return data.get("results", data)

    async def generate_report(
        self,
        report_type: str,
        candidate_id: int | None = None,
    ) -> dict:
        """Сгенерировать отчёт."""
        payload = {"report_type": report_type}
        if candidate_id:
            payload["candidate_id"] = candidate_id
        return await self._request("POST", "reports/generate/", json=payload)

    async def get_report(self, report_id: int) -> dict:
        """Получить детали отчёта по ID."""
        return await self._request("GET", f"reports/{report_id}/")

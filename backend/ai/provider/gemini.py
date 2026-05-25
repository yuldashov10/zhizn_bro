import json
import logging

from ai.prompts.event_analysis import EventAnalysisPrompt
from ai.provider.base import (
    BaseAIProvider,
    CriterionScore,
    EventAnalysisResult,
)
from ai.schemas.responses import EventAnalysisSchema
from core.exceptions.base import ProviderError
from decouple import config
from google import genai
from google.genai import types

logger = logging.getLogger("ai")


class GeminiProvider(BaseAIProvider):
    """
    AI провайдер на базе Google Gemini.
    Использует gemini-1.5-flash для анализа событий.
    """

    MODEL_NAME = "gemini-1.5-flash"

    def __init__(self) -> None:
        api_key = config("GEMINI_API_KEY", cast=str)
        self._client = genai.Client(api_key=api_key)

    def analyze_event(
        self,
        raw_text: str,
        user_context: dict,
        criteria: list[str],
        hard_stops: list[str],
    ) -> EventAnalysisResult:
        """Анализирует событие через Gemini API."""
        prompt = EventAnalysisPrompt(
            raw_text=raw_text,
            user_context=user_context,
            criteria=criteria,
            hard_stops=hard_stops,
        ).build()

        try:
            response = self._client.models.generate_content(
                model=self.MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    top_p=0.8,
                    max_output_tokens=1024,
                ),
            )
            return self._parse_response(response.text)
        except Exception as e:
            logger.error(f"Ошибка Gemini API: {e}")
            raise ProviderError(f"Ошибка AI провайдера: {e}") from e

    def detect_attachment_type(self, answers: list[dict]) -> str:
        """Определяет тип привязанности по ответам."""
        anxiety_scores = []
        avoidance_scores = []

        for answer in answers:
            weighted = answer["answer"] * answer["weight"]
            if answer["dimension"] == "anxiety":
                anxiety_scores.append(weighted)
            else:
                avoidance_scores.append(weighted)

        avg_anxiety = (
            sum(anxiety_scores) / len(anxiety_scores) if anxiety_scores else 0
        )
        avg_avoidance = (
            sum(avoidance_scores) / len(avoidance_scores)
            if avoidance_scores
            else 0
        )

        if avg_anxiety <= 3 and avg_avoidance <= 3:
            return "secure"
        elif avg_anxiety > 3 and avg_avoidance <= 3:
            return "anxious"
        elif avg_anxiety <= 3 and avg_avoidance > 3:
            return "avoidant"
        else:
            return "disorganized"

    def _parse_response(self, text: str) -> EventAnalysisResult:
        """
        Парсит JSON ответ от Gemini.
        Валидирует через Pydantic схему.
        """
        try:
            clean = text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            data = json.loads(clean)
            schema = EventAnalysisSchema(**data)

            return EventAnalysisResult(
                scores=[
                    CriterionScore(
                        criterion_name=s.criterion_name,
                        score=s.score,
                        reasoning=s.reasoning,
                    )
                    for s in schema.scores
                ],
                interpretation=schema.interpretation,
                bias_warning=schema.bias_warning,
                is_hard_stop=schema.is_hard_stop,
                hard_stop_name=schema.hard_stop_name,
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка парсинга ответа Gemini: {e}\nТекст: {text}")
            raise ProviderError(
                f"Некорректный ответ от AI провайдера: {e}"
            ) from e

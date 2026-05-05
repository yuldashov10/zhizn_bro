import json
import logging

from ai.prompts.event_analysis import build_event_analysis_prompt
from ai.provider.base import (
    BaseAIProvider,
    CriterionScore,
    EventAnalysisResult,
)
from ai.schemas.responses import EventAnalysisSchema
from core.exceptions.base import ProviderError
from decouple import config
from groq import Groq

logger = logging.getLogger("ai")


class GroqProvider(BaseAIProvider):
    """
    AI провайдер на базе Groq.
    Использует llama-3.3-70b для анализа событий.
    """

    MODEL_NAME = "llama-3.3-70b-versatile"

    def __init__(self) -> None:
        api_key = config("GROQ_API_KEY", cast=str)
        self._client = Groq(api_key=api_key)

    def analyze_event(
        self,
        raw_text: str,
        user_context: dict,
        criteria: list[str],
        hard_stops: list[str],
    ) -> EventAnalysisResult:
        """Анализирует событие через Groq API."""
        prompt = build_event_analysis_prompt(
            raw_text=raw_text,
            user_context=user_context,
            criteria=criteria,
            hard_stops=hard_stops,
        )

        try:
            response = self._client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты — эксперт по когнитивной "
                            "психологии и анализу отношений. "
                            "Всегда отвечай строго в "
                            "формате JSON без markdown блоков."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            return self._parse_response(text), tokens_used

        except Exception as e:
            logger.error(f"Ошибка Groq API: {e}")
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
        Парсит JSON ответ от Groq.
        Groq с response_format=json_object гарантирует валидный JSON.
        """
        try:
            data = json.loads(text)
            logger.debug(f"Ответ Groq: {data}")
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
            logger.error(f"Ошибка парсинга ответа Groq: {e}\nТекст: {text}")
            raise ProviderError(
                f"Некорректный ответ от AI провайдера: {e}"
            ) from e

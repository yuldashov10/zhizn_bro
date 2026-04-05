from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CriterionScore:
    """Оценка события по одному критерию."""

    criterion_name: str
    score: int
    reasoning: str


@dataclass
class EventAnalysisResult:
    """Результат анализа события от AI провайдера."""

    scores: list[CriterionScore]
    interpretation: str
    bias_warning: str
    is_hard_stop: bool
    hard_stop_name: str | None


class BaseAIProvider(ABC):
    """
    Базовый класс AI провайдера.
    Все провайдеры должны реализовать этот интерфейс.
    """

    @abstractmethod
    def analyze_event(
        self,
        raw_text: str,
        user_context: dict,
        criteria: list[str],
        hard_stops: list[str],
    ) -> EventAnalysisResult:
        """
        Анализирует событие и возвращает структурированный результат.

        Args:
            raw_text:     текст события от пользователя
            user_context: профиль пользователя (тип привязанности и т.д.)
            criteria:     список активных критериев пользователя
            hard_stops:   список активных Hard Stops пользователя
        """

    @abstractmethod
    def detect_attachment_type(
        self,
        answers: list[dict],
    ) -> str:
        """
        Определяет тип привязанности по ответам на тест.

        Args:
            answers: список ответов [{question, dimension, answer, weight}]
        """

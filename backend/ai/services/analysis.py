import logging

from ai.provider.base import EventAnalysisResult
from ai.provider.factory import AIProviderFactory
from decouple import config
from django.db import models

from apps.criteria.models import Criterion, HardStop
from apps.events.models import AIProviderLog, Event, EventCriterionScore
from apps.users.models import User
from core.exceptions.base import ProviderError

logger = logging.getLogger("ai")


class AIAnalysisService:
    """
    Сервис AI анализа событий.
    Связывает AI провайдера с бизнес-логикой приложения.
    """

    @classmethod
    def analyze(cls, event: Event) -> Event:
        """
        Анализирует событие через AI провайдера.
        Сохраняет результат в БД и логирует токены.
        """
        user = event.candidate.user
        provider = AIProviderFactory.get_provider()

        user_context = cls._build_user_context(user)
        criteria = cls._get_active_criteria(user)
        hard_stops = cls._get_active_hard_stops(user)

        try:
            result, tokens_used = provider.analyze_event(
                raw_text=event.raw_text,
                user_context=user_context,
                criteria=[c.name for c in criteria],
                hard_stops=[h.name for h in hard_stops],
            )
        except ProviderError:
            logger.error(f"Не удалось проанализировать событие {event.pk}")
            raise

        cls._save_result(event, result, criteria, hard_stops)
        cls._log_request(event, result, tokens_used)

        return event

    @classmethod
    def _build_user_context(cls, user: User) -> dict:
        """Строит контекст пользователя для промпта."""
        profile = getattr(user, "profile", None)
        return {
            "attachment_type": (
                profile.get_attachment_type_display()
                if profile and profile.attachment_type
                else "не определён"
            ),
            "correction_coefficient": (
                profile.correction_coefficient if profile else 1.0
            ),
        }

    @classmethod
    def _get_active_criteria(cls, user) -> list[Criterion]:
        """Возвращает активные критерии с учётом настроек пользователя."""
        from apps.criteria.models import UserCriterionSettings

        all_criteria = list(Criterion.objects.filter(is_default=True))
        user_settings = {
            s.criterion_id: s.is_active
            for s in UserCriterionSettings.objects.filter(user=user)
        }
        return [c for c in all_criteria if user_settings.get(c.pk, True)]

    @classmethod
    def _get_active_hard_stops(cls, user) -> list[HardStop]:
        """Возвращает активные Hard Stops с учётом настроек пользователя."""
        from apps.criteria.models import UserHardStopSettings

        all_hard_stops = list(HardStop.objects.filter(is_default=True))
        user_settings = {
            s.hard_stop_id: s.is_active
            for s in UserHardStopSettings.objects.filter(user=user)
        }
        return [h for h in all_hard_stops if user_settings.get(h.pk, True)]

    @classmethod
    def _save_result(
        cls,
        event: Event,
        result: EventAnalysisResult,
        criteria: list[Criterion],
        hard_stops: list[HardStop],
    ) -> None:
        """Сохраняет результат анализа в БД."""
        criteria_map = {c.name.lower(): c for c in criteria}

        for score in result.scores:
            criterion = criteria_map.get(score.criterion_name.lower())
            if not criterion:
                logger.warning(
                    f"Критерий '{score.criterion_name}' не найден в БД"
                )
                continue

            EventCriterionScore.objects.update_or_create(
                event=event,
                criterion=criterion,
                defaults={
                    "ai_score": score.score,
                    "is_confirmed": False,
                },
            )

        # Проверяем Hard Stop через БД (не доверяем только ИИ)
        is_hard_stop = False
        if result.is_hard_stop and result.hard_stop_name:
            hard_stop = next(
                (
                    h
                    for h in hard_stops
                    if h.name.lower() == result.hard_stop_name.lower()
                ),
                None,
            )
            if hard_stop:
                is_hard_stop = True
                from apps.candidates.models import CandidateHardStopLog

                CandidateHardStopLog.objects.create(
                    candidate=event.candidate,
                    hard_stop=hard_stop,
                    note=event.raw_text,
                )
                event.candidate.hard_stop_triggered = True
                event.candidate.save(update_fields=["hard_stop_triggered"])

        event.ai_interpretation = result.interpretation
        event.bias_warning = result.bias_warning
        event.is_hard_stop = is_hard_stop
        event.save(
            update_fields=[
                "ai_interpretation",
                "bias_warning",
                "is_hard_stop",
            ]
        )

    @classmethod
    def _log_request(
        cls,
        event: Event,
        result: EventAnalysisResult,
        tokens_used: int = 0,
    ) -> None:
        """Логирует запрос к AI провайдеру."""
        AIProviderLog.objects.create(
            event=event,
            provider=config("AI_PROVIDER", default="groq"),
            prompt=event.raw_text,
            response=result.interpretation,
            tokens_used=tokens_used,
        )

        from apps.users.models import UserTokenLimit

        UserTokenLimit.objects.filter(
            user=event.candidate.user,
        ).update(
            used_today=models.F("used_today") + tokens_used,
            used_this_month=models.F("used_this_month") + tokens_used,
        )

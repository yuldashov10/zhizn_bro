import pytest

from apps.assessments.models import (
    AttachmentTest,
    Question,
    UserAnswer,
    UserTestSession,
)
from apps.candidates.models import (
    Candidate,
    CandidateHardStopLog,
    CandidateStatusHistory,
)
from apps.criteria.models import Criterion, HardStop
from apps.events.models import AIProviderLog, Event, EventCriterionScore
from apps.reports.models import ReportLog
from apps.users.models import User, UserProfile, UserTokenLimit


@pytest.fixture
def user(db):
    return User.objects.create_user(
        telegram_id=555555555, username="integration_user"
    )


@pytest.fixture
def candidate(user):
    return Candidate.objects.create(
        user=user,
        name="Интеграционный кандидат",
        is_active=True,
    )


@pytest.fixture
def criterion(db):
    return Criterion.objects.create(
        name="Доверие",
        weight=0.30,
        is_default=True,
        is_active=True,
    )


@pytest.fixture
def hard_stop(db):
    return HardStop.objects.create(
        name="Ложь / обман",
        is_default=True,
        is_active=True,
    )


@pytest.fixture
def event(candidate):
    return Event.objects.create(
        candidate=candidate,
        raw_text="Тестовое событие",
    )


class TestUserCascade:
    def test_delete_user_deletes_profile(self, user):
        """Удаление пользователя удаляет профиль."""
        UserProfile.objects.create(
            user=user,
            attachment_type=UserProfile.AttachmentType.SECURE,
            attachment_source=UserProfile.AttachmentSource.BOT_TEST,
        )
        user_id = user.pk
        user.delete()
        assert not UserProfile.objects.filter(user_id=user_id).exists()

    def test_delete_user_deletes_token_limit(self, user):
        """Удаление пользователя удаляет лимиты токенов."""
        UserTokenLimit.objects.create(user=user)
        user_id = user.pk
        user.delete()
        assert not UserTokenLimit.objects.filter(user_id=user_id).exists()

    def test_delete_user_deletes_candidates(self, user, candidate):
        """Удаление пользователя удаляет всех кандидатов."""
        user_id = user.pk
        user.delete()
        assert not Candidate.objects.filter(user_id=user_id).exists()


class TestCandidateCascade:
    def test_delete_candidate_deletes_status_history(self, candidate):
        """Удаление кандидата удаляет историю статусов."""
        CandidateStatusHistory.objects.create(
            candidate=candidate,
            status=CandidateStatusHistory.Status.MEETING,
        )
        candidate_id = candidate.pk
        candidate.delete()
        assert not CandidateStatusHistory.objects.filter(
            candidate_id=candidate_id
        ).exists()

    def test_delete_candidate_deletes_events(self, candidate, event):
        """Удаление кандидата удаляет все события."""
        candidate_id = candidate.pk
        candidate.delete()
        assert not Event.objects.filter(candidate_id=candidate_id).exists()

    def test_delete_candidate_deletes_hard_stop_logs(
        self, candidate, hard_stop
    ):
        """Удаление кандидата удаляет логи Hard Stop."""
        CandidateHardStopLog.objects.create(
            candidate=candidate,
            hard_stop=hard_stop,
        )
        candidate_id = candidate.pk
        candidate.delete()
        assert not CandidateHardStopLog.objects.filter(
            candidate_id=candidate_id
        ).exists()


class TestEventCascade:
    def test_delete_event_deletes_scores(self, event, criterion):
        """Удаление события удаляет оценки по критериям."""
        EventCriterionScore.objects.create(
            event=event,
            criterion=criterion,
            ai_score=1,
        )
        event_id = event.pk
        event.delete()
        assert not EventCriterionScore.objects.filter(
            event_id=event_id
        ).exists()

    def test_delete_event_nullifies_ai_log(self, event):
        """Удаление события обнуляет ссылку в логе AI (SET_NULL)."""
        log = AIProviderLog.objects.create(
            event=event,
            provider=AIProviderLog.Provider.CLAUDE,
            prompt="Тест",
            response="Ответ",
            tokens_used=100,
        )
        event.delete()
        log.refresh_from_db()
        assert log.event is None


class TestAssessmentCascade:
    def test_delete_test_deletes_questions(self, db):
        """Удаление теста удаляет все вопросы."""
        test = AttachmentTest.objects.create(
            name="Тест для удаления",
            is_validated=False,
            is_active=True,
        )
        Question.objects.create(
            test=test,
            text="Тестовый вопрос",
            dimension=Question.Dimension.ANXIETY,
            order=1,
        )
        test_id = test.pk
        test.delete()
        assert not Question.objects.filter(test_id=test_id).exists()

    def test_delete_session_deletes_answers(self, user, db):
        """Удаление сессии удаляет все ответы."""
        test = AttachmentTest.objects.create(
            name="Тест сессии",
            is_validated=False,
            is_active=True,
        )
        question = Question.objects.create(
            test=test,
            text="Вопрос",
            dimension=Question.Dimension.ANXIETY,
            order=1,
        )
        session = UserTestSession.objects.create(
            user=user,
            test=test,
            result_type=UserTestSession.AttachmentResult.SECURE,
        )
        UserAnswer.objects.create(
            session=session,
            question=question,
            answer=3,
        )
        session_id = session.pk
        session.delete()
        assert not UserAnswer.objects.filter(session_id=session_id).exists()


class TestReportLog:
    def test_delete_candidate_nullifies_report(self, user, candidate):
        """Удаление кандидата обнуляет ссылку в отчёте (SET_NULL)."""
        report = ReportLog.objects.create(
            user=user,
            candidate=candidate,
            report_type=ReportLog.ReportType.PDF,
            trigger=ReportLog.Trigger.MANUAL,
        )
        candidate.delete()
        report.refresh_from_db()
        assert report.candidate is None

    def test_delete_user_deletes_reports(self, user, candidate):
        """Удаление пользователя удаляет все отчёты."""
        ReportLog.objects.create(
            user=user,
            candidate=None,
            report_type=ReportLog.ReportType.TEXT,
            trigger=ReportLog.Trigger.MANUAL,
        )
        user_id = user.pk
        user.delete()
        assert not ReportLog.objects.filter(user_id=user_id).exists()


class TestScoringIntegration:
    def test_scoring_with_multiple_events_per_criterion(
        self, candidate, criterion
    ):
        """Скор усредняет несколько событий по одному критерию."""
        from apps.events.services import ScoringService

        for score in [2, 0, -2]:
            event = Event.objects.create(
                candidate=candidate,
                raw_text=f"Событие со скором {score}",
            )
            EventCriterionScore.objects.create(
                event=event,
                criterion=criterion,
                ai_score=score,
                is_confirmed=True,
            )

        result = ScoringService.calculate(candidate)
        assert result == 50

    def test_scoring_respects_weights(self, user, db):
        """Скор учитывает веса критериев."""
        from apps.events.services import ScoringService

        candidate = Candidate.objects.create(
            user=user,
            name="Весовой тест",
            is_active=True,
        )
        heavy = Criterion.objects.create(
            name="Тяжёлый критерий",
            weight=0.80,
            is_default=False,
            is_active=True,
        )
        light = Criterion.objects.create(
            name="Лёгкий критерий",
            weight=0.20,
            is_default=False,
            is_active=True,
        )

        # Тяжёлый критерий — максимум, лёгкий — минимум
        for criterion, score in [(heavy, 2), (light, -2)]:
            event = Event.objects.create(
                candidate=candidate,
                raw_text=f"Событие {criterion.name}",
            )
            EventCriterionScore.objects.create(
                event=event,
                criterion=criterion,
                ai_score=score,
                is_confirmed=True,
            )

        result = ScoringService.calculate(candidate)
        # 0.80*2 + 0.20*(-2) = 1.2 → нормализация → > 50
        assert result > 50

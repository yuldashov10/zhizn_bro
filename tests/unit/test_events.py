import pytest

from apps.candidates.models import Candidate
from apps.criteria.models import Criterion
from apps.events.models import Event, EventCriterionScore
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        telegram_id=333333333, username="event_user"
    )


@pytest.fixture
def candidate(user):
    return Candidate.objects.create(
        user=user,
        name="Тестовый кандидат",
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
def event(candidate):
    return Event.objects.create(
        candidate=candidate,
        raw_text="Обещала позвонить и не позвонила",
        ai_interpretation="Нарушение обещания",
        is_hard_stop=False,
        bias_warning="",
    )


class TestEvent:
    def test_str(self, event):
        assert "Обещала позвонить" in str(event)

    def test_has_bias_warning_false(self, event):
        assert event.has_bias_warning() is False

    def test_has_bias_warning_true(self, event):
        event.bias_warning = "Возможно это твоя тревожность"
        assert event.has_bias_warning() is True

    def test_default_is_hard_stop_false(self, event):
        assert event.is_hard_stop is False


class TestEventCriterionScore:
    def test_final_score_uses_ai_when_no_user_score(self, event, criterion):
        score = EventCriterionScore.objects.create(
            event=event,
            criterion=criterion,
            ai_score=-1,
            user_score=None,
            is_confirmed=False,
        )
        assert score.final_score == -1

    def test_final_score_uses_user_score_when_set(self, event, criterion):
        score = EventCriterionScore.objects.create(
            event=event,
            criterion=criterion,
            ai_score=-1,
            user_score=1,
            is_confirmed=True,
        )
        assert score.final_score == 1

    def test_final_score_user_score_zero(self, event, criterion):
        """Проверяет что user_score=0 не считается как None."""
        score = EventCriterionScore.objects.create(
            event=event,
            criterion=criterion,
            ai_score=-2,
            user_score=0,
            is_confirmed=True,
        )
        assert score.final_score == 0

    def test_score_bounds(self, event, criterion):
        from django.core.exceptions import ValidationError

        score = EventCriterionScore(
            event=event,
            criterion=criterion,
            ai_score=5,
        )
        with pytest.raises(ValidationError):
            score.full_clean()

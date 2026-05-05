import pytest

from apps.candidates.models import Candidate
from apps.criteria.models import Criterion
from apps.events.models import Event, EventCriterionScore
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        telegram_id=444444444, username="scoring_user"
    )


@pytest.fixture
def candidate(user):
    return Candidate.objects.create(
        user=user,
        name="Тест Скоринга",
        is_active=True,
    )


@pytest.fixture
def criteria(db):
    data = [
        ("Доверие", 0.30),
        ("Эмоц. стабильность", 0.25),
        ("Уважение", 0.20),
        ("Открытость", 0.15),
        ("Интеллект", 0.10),
    ]
    return [
        Criterion.objects.create(
            name=name,
            weight=weight,
            is_default=True,
            is_active=True,
        )
        for name, weight in data
    ]


def create_event_with_score(candidate, criterion, ai_score, user_score=None):
    """Вспомогательная функция создания события с оценкой."""
    event = Event.objects.create(
        candidate=candidate,
        raw_text=f"Тестовое событие для {criterion.name}",
    )
    EventCriterionScore.objects.create(
        event=event,
        criterion=criterion,
        ai_score=ai_score,
        user_score=user_score,
        is_confirmed=True,
    )
    return event


class TestScoringService:
    def test_perfect_score(self, candidate, criteria):
        """Все оценки +2 должны давать 100."""
        from apps.events.services import ScoringService

        for criterion in criteria:
            create_event_with_score(candidate, criterion, ai_score=2)
        score = ScoringService.calculate(candidate)
        assert score == 100

    def test_worst_score(self, candidate, criteria):
        """Все оценки -2 должны давать 0."""
        from apps.events.services import ScoringService

        for criterion in criteria:
            create_event_with_score(candidate, criterion, ai_score=-2)
        score = ScoringService.calculate(candidate)
        assert score == 0

    def test_neutral_score(self, candidate, criteria):
        """Все оценки 0 должны давать 50."""
        from apps.events.services import ScoringService

        for criterion in criteria:
            create_event_with_score(candidate, criterion, ai_score=0)
        score = ScoringService.calculate(candidate)
        assert score == 50

    def test_user_score_takes_priority(self, candidate, criteria):
        """Если пользователь скорректировал — используется его оценка."""
        from apps.events.services import ScoringService

        criterion = criteria[0]
        create_event_with_score(
            candidate,
            criterion,
            ai_score=-2,
            user_score=2,
        )
        score = ScoringService.calculate(candidate)
        assert score > 50

    def test_score_in_valid_range(self, candidate, criteria):
        """Скор всегда в диапазоне 0–100."""
        from apps.events.services import ScoringService

        for criterion in criteria:
            create_event_with_score(candidate, criterion, ai_score=1)
        score = ScoringService.calculate(candidate)
        assert 0 <= score <= 100

    def test_no_events_returns_none(self, candidate):
        """Без событий скор не может быть рассчитан."""
        from apps.events.services import ScoringService

        score = ScoringService.calculate(candidate)
        assert score is None

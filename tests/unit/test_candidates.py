import pytest

from apps.candidates.models import Candidate, CandidateStatusHistory
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        telegram_id=222222222, username="candidate_user"
    )


@pytest.fixture
def candidate(user):
    return Candidate.objects.create(
        user=user,
        name="Алия",
        age=25,
        met_at="Приложение для знакомств",
        is_active=True,
    )


class TestCandidate:
    def test_str(self, candidate):
        assert "Алия" in str(candidate)

    def test_archive(self, candidate):
        assert candidate.is_active is True
        candidate.archive()
        assert candidate.is_active is False

    def test_archive_saves_to_db(self, candidate):
        candidate.archive()
        refreshed = Candidate.objects.get(pk=candidate.pk)
        assert refreshed.is_active is False

    def test_default_hard_stop_not_triggered(self, candidate):
        assert candidate.hard_stop_triggered is False

    def test_ai_attachment_type_nullable(self, candidate):
        assert candidate.ai_attachment_type is None


class TestCandidateStatusHistory:
    def test_str(self, candidate):
        status = CandidateStatusHistory.objects.create(
            candidate=candidate,
            status=CandidateStatusHistory.Status.MEETING,
            note="Начало знакомства",
        )
        assert "Алия" in str(status)
        assert "Знакомство" in str(status)

    def test_multiple_statuses(self, candidate):
        CandidateStatusHistory.objects.create(
            candidate=candidate,
            status=CandidateStatusHistory.Status.MEETING,
        )
        CandidateStatusHistory.objects.create(
            candidate=candidate,
            status=CandidateStatusHistory.Status.DATING,
        )
        assert candidate.status_history.count() == 2

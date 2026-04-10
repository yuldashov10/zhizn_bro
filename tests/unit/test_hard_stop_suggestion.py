import pytest

from apps.criteria.models import HardStop, HardStopSuggestion
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        telegram_id=777777777,
        username="suggestion_user",
    )


@pytest.fixture
def suggestion(user):
    return HardStopSuggestion.objects.create(
        user=user,
        text="Наличие домашних животных которых боюсь",
    )


class TestHardStopSuggestion:
    def test_default_status_is_pending(self, suggestion):
        assert suggestion.status == HardStopSuggestion.Status.PENDING

    def test_str(self, suggestion):
        assert "suggestion_user" in str(suggestion)
        assert "домашних животных" in str(suggestion)

    def test_approve(self, suggestion):
        suggestion.status = HardStopSuggestion.Status.APPROVED
        suggestion.save()
        assert suggestion.status == HardStopSuggestion.Status.APPROVED

    def test_reject_with_note(self, suggestion):
        suggestion.status = HardStopSuggestion.Status.REJECTED
        suggestion.admin_note = "Слишком специфично"
        suggestion.save()
        refreshed = HardStopSuggestion.objects.get(pk=suggestion.pk)
        assert refreshed.status == HardStopSuggestion.Status.REJECTED
        assert refreshed.admin_note == "Слишком специфично"

    def test_user_can_have_multiple_suggestions(self, user):
        HardStopSuggestion.objects.create(user=user, text="Первое предложение")
        HardStopSuggestion.objects.create(user=user, text="Второе предложение")
        assert HardStopSuggestion.objects.filter(user=user).count() == 2

    def test_delete_user_deletes_suggestions(self, user, suggestion):
        user_id = user.pk
        user.delete()
        assert not HardStopSuggestion.objects.filter(user_id=user_id).exists()

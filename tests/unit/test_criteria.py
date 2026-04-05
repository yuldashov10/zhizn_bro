import pytest

from apps.criteria.models import Criterion, HardStop
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        telegram_id=111111111, username="criteria_user"
    )


@pytest.fixture
def system_hard_stop(db):
    return HardStop.objects.create(
        name="Ложь / обман",
        description="Нулевая терпимость",
        is_default=True,
        is_active=True,
        user=None,
    )


@pytest.fixture
def user_hard_stop(user):
    return HardStop.objects.create(
        name="Пользовательский фильтр",
        description="Кастомный фильтр",
        is_default=False,
        is_active=True,
        user=user,
    )


@pytest.fixture
def system_criterion(db):
    return Criterion.objects.create(
        name="Доверие",
        weight=0.30,
        description="Честность и выполнение обещаний",
        is_default=True,
        is_active=True,
        user=None,
    )


class TestHardStop:
    def test_system_hard_stop_is_system(self, system_hard_stop):
        assert system_hard_stop.is_system() is True

    def test_user_hard_stop_is_not_system(self, user_hard_stop):
        assert user_hard_stop.is_system() is False

    def test_str_system(self, system_hard_stop):
        assert "[Системный]" in str(system_hard_stop)
        assert "Ложь / обман" in str(system_hard_stop)

    def test_str_user(self, user_hard_stop):
        assert "[Системный]" not in str(user_hard_stop)
        assert "Пользовательский фильтр" in str(user_hard_stop)

    def test_inactive_hard_stop(self, system_hard_stop):
        system_hard_stop.is_active = False
        assert not system_hard_stop.is_active


class TestCriterion:
    def test_system_criterion_is_system(self, system_criterion):
        assert system_criterion.is_system() is True

    def test_str_contains_percentage(self, system_criterion):
        assert "30%" in str(system_criterion)

    def test_str_contains_name(self, system_criterion):
        assert "Доверие" in str(system_criterion)

    def test_weight_bounds(self, db):
        from django.core.exceptions import ValidationError

        criterion = Criterion(
            name="Тест",
            weight=1.5,
            is_default=False,
            is_active=True,
        )
        with pytest.raises(ValidationError):
            criterion.full_clean()

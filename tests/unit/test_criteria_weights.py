import pytest

from apps.criteria.models import Criterion
from apps.criteria.services import CriteriaWeightService
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        telegram_id=888888888,
        username="weights_user",
    )


@pytest.fixture
def system_criteria(db):
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


class TestCriteriaWeightService:
    def test_all_active_weights_sum_to_one(self, system_criteria):
        """Сумма весов всех активных критериев = 1.0"""
        weights = CriteriaWeightService.get_effective_weights(system_criteria)
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_disable_one_redistributes_weights(self, system_criteria):
        """Отключение критерия перераспределяет его вес."""
        active = [c for c in system_criteria if c.name != "Интеллект"]
        weights = CriteriaWeightService.get_effective_weights(active)
        assert abs(sum(weights.values()) - 1.0) < 0.001
        assert "Интеллект" not in weights

    def test_disabled_criterion_weight_distributed_proportionally(
        self, system_criteria
    ):
        """Вес отключённого критерия распределяется пропорционально."""
        # Отключаем Интеллект (0.10)
        active = [c for c in system_criteria if c.name != "Интеллект"]
        weights = CriteriaWeightService.get_effective_weights(active)

        # Доверие должно вырасти пропорционально: 0.30 / 0.90 ≈ 0.333
        assert abs(weights["Доверие"] - 0.30 / 0.90) < 0.001

    def test_minimum_criteria_count(self, system_criteria):
        """Минимум 3 активных критерия."""
        active = system_criteria[:2]  # только 2
        with pytest.raises(ValueError, match="минимум 3"):
            CriteriaWeightService.get_effective_weights(active)

    def test_single_criterion_raises(self, system_criteria):
        """Один критерий — ошибка."""
        with pytest.raises(ValueError):
            CriteriaWeightService.get_effective_weights(system_criteria[:1])

    def test_empty_criteria_raises(self, db):
        """Пустой список — ошибка."""
        with pytest.raises(ValueError):
            CriteriaWeightService.get_effective_weights([])

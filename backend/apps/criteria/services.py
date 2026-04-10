from apps.criteria.models import Criterion


class CriteriaWeightService:
    """
    Сервис управления весами критериев.
    При отключении критерия автоматически перераспределяет веса.
    """

    MIN_CRITERIA = 3

    @classmethod
    def get_effective_weights(
        cls,
        active_criteria: list[Criterion],
    ) -> dict[str, float]:
        """
        Рассчитывает эффективные веса для активных критериев.
        Сумма весов всегда равна 1.0.

        Args:
            active_criteria: список активных критериев

        Returns:
            dict: {criterion_name: effective_weight}

        Raises:
            ValueError: если активных критериев меньше минимума
        """
        if len(active_criteria) < cls.MIN_CRITERIA:
            raise ValueError(
                f"Необходимо минимум {cls.MIN_CRITERIA} активных критерия, "
                f"получено: {len(active_criteria)}"
            )

        total_weight = sum(c.weight for c in active_criteria)

        if total_weight == 0:
            raise ValueError("Сумма весов активных критериев равна нулю")

        return {
            c.name: round(c.weight / total_weight, 4) for c in active_criteria
        }

    @classmethod
    def can_disable(
        cls,
        user_active_criteria: list[Criterion],
    ) -> bool:
        """
        Проверяет можно ли отключить ещё один критерий.
        Нельзя если останется меньше минимума.
        """
        return len(user_active_criteria) > cls.MIN_CRITERIA

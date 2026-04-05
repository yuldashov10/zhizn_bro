from apps.candidates.models import Candidate
from apps.events.models import EventCriterionScore


class ScoringService:
    """
    Сервис расчёта итогового скора кандидата.

    Формула:
        Score = SUM( avg(criterion_scores) * weight ) * 25 + 50

    Где criterion_scores — финальные баллы (-2..+2) по каждому критерию.
    Результат нормализован в диапазон 0–100.
    """

    MIN_SCORE = -2
    MAX_SCORE = 2
    SCORE_RANGE = MAX_SCORE - MIN_SCORE  # 4
    NORMALIZED_MID = 50

    @classmethod
    def calculate(cls, candidate: Candidate) -> int | None:
        """
        Рассчитывает итоговый взвешенный скор кандидата.
        Возвращает None если нет подтверждённых событий.
        """
        scores = cls._get_scores(candidate)
        if not scores:
            return None

        criterion_averages = cls._calculate_criterion_averages(scores)
        if not criterion_averages:
            return None

        weighted_sum = cls._calculate_weighted_sum(criterion_averages)
        return cls._normalize(weighted_sum)

    @classmethod
    def _get_scores(cls, candidate: Candidate) -> list[EventCriterionScore]:
        """Возвращает все оценки событий кандидата."""
        return list(
            EventCriterionScore.objects.filter(
                event__candidate=candidate,
            ).select_related("criterion")
        )

    @classmethod
    def _calculate_criterion_averages(
        cls,
        scores: list[EventCriterionScore],
    ) -> dict[int, dict]:
        """
        Рассчитывает средний балл и вес для каждого критерия.
        Возвращает словарь: {criterion_id: {avg: float, weight: float}}
        """
        criterion_data: dict[int, dict] = {}

        for score in scores:
            criterion_id = score.criterion_id
            if criterion_id not in criterion_data:
                criterion_data[criterion_id] = {
                    "scores": [],
                    "weight": score.criterion.weight,
                }
            criterion_data[criterion_id]["scores"].append(score.final_score)

        return {
            cid: {
                "avg": sum(data["scores"]) / len(data["scores"]),
                "weight": data["weight"],
            }
            for cid, data in criterion_data.items()
        }

    @classmethod
    def _calculate_weighted_sum(
        cls,
        criterion_averages: dict[int, dict],
    ) -> float:
        """Рассчитывает взвешенную сумму средних баллов."""
        return sum(
            data["avg"] * data["weight"]
            for data in criterion_averages.values()
        )

    @classmethod
    def _normalize(cls, weighted_sum: float) -> int:
        """
        Нормализует взвешенную сумму в диапазон 0–100.
        weighted_sum=-2 → 0, weighted_sum=0 → 50, weighted_sum=+2 → 100
        """
        normalized = (
            weighted_sum / cls.MAX_SCORE
        ) * cls.NORMALIZED_MID + cls.NORMALIZED_MID
        return int(max(0, min(100, round(normalized))))

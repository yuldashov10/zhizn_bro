from dataclasses import dataclass


@dataclass
class EventAnalysisPrompt:
    """
    Строитель промпта для анализа события.

    Формирует структурированный промпт на русском языке,
    с учётом контекста пользователя, активных критериев и Hard Stops.
    """

    raw_text: str
    user_context: dict
    criteria: list[str]
    hard_stops: list[str]

    SCORE_SCALE = {
        "+2": "сильный позитивный сигнал",
        "+1": "слабый позитивный сигнал",
        "0": "нейтрально",
        "-1": "слабый красный флаг",
        "-2": "сильный красный флаг",
    }

    BIAS_TYPES = [
        "Эффект ореола (только позитивные/негативные события)",
        "Тревожная гиперреакция",
        "Непоследовательность оценок",
    ]

    def __init__(
        self,
        raw_text: str,
        user_context: dict,
        criteria: list[str],
        hard_stops: list[str],
    ) -> None:
        self.raw_text = raw_text
        self.user_context = user_context
        self.criteria = criteria
        self.hard_stops = hard_stops

    def build(self) -> str:
        """Собирает и возвращает готовый промпт."""

        return "\n\n".join(
            [
                self._system_role(),
                self._user_context_section(),
                self._criteria_section(),
                self._hard_stops_section(),
                self._event_section(),
                self._task_section(),
                self._response_format_section(),
            ]
        )

    def _system_role(self) -> str:
        return (
            "Ты – эксперт по когнитивной психологии и анализу отношений.\n"
            "Твоя задача – объективно проанализировать событие, "
            "основываясь на принципах Системы 2 (Даниэль Канеман)."
        )

    def _user_context_section(self) -> str:
        attachment = self.user_context.get(
            "attachment_type", "не определён"
        ).strip()
        correction = self.user_context.get("correction_coefficient", 1.0)

        return (
            "## Контекст пользователя\n"
            f"- Тип привязанности: {attachment}\n"
            f"- Поправочный коэффициент: {correction}\n"
            f"(< 1.0 – склонен к негативным оценкам, "
            f"> 1.0 – склонен к позитивным)"
        )

    def _criteria_section(self) -> str:
        items = "\n".join(f"- {item}" for item in self.criteria)
        return f"## Активные критерии оценки\n{items}"

    def _hard_stops_section(self) -> str:
        items = "\n".join(f"- {item}" for item in self.hard_stops)
        return f"## Hard Stops (абсолютные фильтры)\n{items}"

    def _event_section(self) -> str:
        return f"## Событие для анализа\n{self.raw_text}"

    def _task_section(self) -> str:
        scale = "\n".join(
            f" - {key}: {value}" for key, value in self.SCORE_SCALE.items()
        )
        biases = "\n".join(f" - {item}" for item in self.BIAS_TYPES)

        return (
            "## Твоя задача\n"
            "1. Оцени событие по КАЖДОМУ затронутому критерию "
            "по шкале от -2 до +2:\n"
            f"{scale}\n\n"
            "2. Учти тип привязанности пользователя "
            "(если он указан у пользователя):\n"
            " - Тревожный тип склонен преувеличивать негатив\n"
            " - Избегающий тип склонен преуменьшать значимость\n"
            " - Применяй поправочный коэффициент при оценке\n\n"
            "3. Проверь наличие Hard Stop триггеров\n\n"
            "4. Укажи когнитивное искажение если есть:\n"
            f"{biases}"
        )

    def _response_format_section(self) -> str:
        return (
            "## Формат ответа\n"
            "Верни ТОЛЬКО валидный JSON без markdown блоков:\n"
            "{\n"
            '    "scores": [\n'
            "        {\n"
            '            "criterion_name": "название критерия из списка выше",\n'  # noqa: skip
            '            "score": число от -2 до 2,\n'
            '            "reasoning": "краткое обоснование на русском"\n'
            "        }\n"
            "    ],\n"
            '    "interpretation": "общая интерпретация события на русском",\n'
            '    "bias_warning": "предупреждение о когнитивном искажении или пустая строка",\n'  # noqa: skip
            '    "is_hard_stop": true или false,\n'
            '    "hard_stop_name": "название Hard Stop или null"\n'
            "}"
        )

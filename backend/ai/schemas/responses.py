from pydantic import BaseModel, Field, field_validator


class CriterionScoreSchema(BaseModel):
    """Схема оценки по одному критерию."""

    criterion_name: str = Field(description="Название критерия")
    score: int = Field(description="Балл от -2 до +2", ge=-2, le=2)
    reasoning: str = Field(description="Обоснование оценки")

    @field_validator("criterion_name")
    @classmethod
    def criterion_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Название критерия не может быть пустым")
        return v

    @field_validator("reasoning")
    @classmethod
    def reasoning_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Обоснование не может быть пустым")
        return v


class EventAnalysisSchema(BaseModel):
    """Схема полного ответа AI на анализ события."""

    scores: list[CriterionScoreSchema] = Field(
        description="Оценки по критериям",
        min_length=1,
    )
    interpretation: str = Field(
        description="Общая интерпретация события",
    )
    bias_warning: str = Field(
        default="",
        description="Предупреждение о когнитивном искажении",
    )
    is_hard_stop: bool = Field(
        default=False,
        description="Триггернул ли Hard Stop",
    )
    hard_stop_name: str | None = Field(
        default=None,
        description="Название сработавшего Hard Stop",
    )

    @field_validator("interpretation")
    @classmethod
    def interpretation_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Интерпретация не может быть пустой")
        return v

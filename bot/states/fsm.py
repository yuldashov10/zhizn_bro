from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния регистрации пользователя."""

    waiting_for_language = State()


class CandidateStates(StatesGroup):
    """Состояния добавления и управления кандидатом."""

    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_met_at = State()
    waiting_for_photo = State()
    confirming = State()


class EventStates(StatesGroup):
    """Состояния добавления события."""

    waiting_for_candidate = State()
    waiting_for_text = State()
    confirming_ai_score = State()


class AssessmentStates(StatesGroup):
    """Состояния прохождения теста привязанности."""

    choosing_test = State()
    answering = State()
    confirming_result = State()


class ReportStates(StatesGroup):
    """Состояния генерации отчёта."""

    choosing_candidate = State()
    choosing_type = State()


class CandidateStatusStates(StatesGroup):
    """Состояния смены статуса кандидата."""

    choosing_candidate = State()
    choosing_status = State()
    waiting_for_note = State()

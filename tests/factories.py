import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from apps.assessments.models import AttachmentTest
from apps.candidates.models import Candidate
from apps.criteria.models import Criterion, HardStop
from apps.events.models import Event, EventCriterionScore
from apps.reports.models import ReportLog
from apps.users.models import UserProfile, UserTokenLimit

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Фабрика пользователей."""

    class Meta:
        model = User

    telegram_id = factory.Sequence(lambda n: 100_000_000 + n)
    username = factory.Sequence(lambda n: f"user_{n}")
    language = "ru"


class UserProfileFactory(DjangoModelFactory):
    """Фабрика профилей пользователей."""

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    attachment_type = UserProfile.AttachmentType.SECURE
    attachment_source = UserProfile.AttachmentSource.BOT_TEST
    correction_coefficient = 1.0


class UserTokenLimitFactory(DjangoModelFactory):
    """Фабрика лимитов токенов."""

    class Meta:
        model = UserTokenLimit

    user = factory.SubFactory(UserFactory)
    daily_limit = 10_000
    monthly_limit = 100_000
    used_today = 0
    used_this_month = 0
    tier = UserTokenLimit.Tier.FREE


class HardStopFactory(DjangoModelFactory):
    """Фабрика Hard Stops."""

    class Meta:
        model = HardStop

    name = factory.Sequence(lambda n: f"Hard Stop {n}")
    description = factory.Faker("sentence", locale="ru_RU")
    is_default = True
    is_active = True
    user = None


class CriterionFactory(DjangoModelFactory):
    """Фабрика критериев оценки."""

    class Meta:
        model = Criterion

    name = factory.Sequence(lambda n: f"Критерий {n}")
    weight = 0.20
    description = factory.Faker("sentence", locale="ru_RU")
    is_default = True
    is_active = True
    user = None


class CandidateFactory(DjangoModelFactory):
    """Фабрика кандидатов."""

    class Meta:
        model = Candidate

    user = factory.SubFactory(UserFactory)
    name = factory.Faker("first_name_female", locale="ru_RU")
    age = factory.Faker("random_int", min=20, max=35)
    met_at = factory.Faker("sentence", locale="ru_RU")
    is_active = True


class EventFactory(DjangoModelFactory):
    """Фабрика событий."""

    class Meta:
        model = Event

    candidate = factory.SubFactory(CandidateFactory)
    raw_text = factory.Faker("sentence", locale="ru_RU")
    ai_interpretation = factory.Faker("sentence", locale="ru_RU")
    is_hard_stop = False
    bias_warning = ""


class EventCriterionScoreFactory(DjangoModelFactory):
    """Фабрика оценок событий."""

    class Meta:
        model = EventCriterionScore

    event = factory.SubFactory(EventFactory)
    criterion = factory.SubFactory(CriterionFactory)
    ai_score = 1
    is_confirmed = False


class AttachmentTestFactory(DjangoModelFactory):
    """Фабрика тестов привязанности."""

    class Meta:
        model = AttachmentTest

    name = factory.Sequence(lambda n: f"Тест {n}")
    description = factory.Faker("sentence", locale="ru_RU")
    questions_count = 5
    is_validated = False
    is_active = True


class ReportLogFactory(DjangoModelFactory):
    """Фабрика логов отчётов."""

    class Meta:
        model = ReportLog

    user = factory.SubFactory(UserFactory)
    candidate = factory.SubFactory(CandidateFactory)
    report_type = ReportLog.ReportType.TEXT
    trigger = ReportLog.Trigger.MANUAL

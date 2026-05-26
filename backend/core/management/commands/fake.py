import random

from django.core.management.base import BaseCommand
from faker import Faker

from apps.assessments.models import (
    AttachmentTest,
    UserAnswer,
    UserTestSession,
)
from apps.candidates.models import (
    Candidate,
    CandidateHardStopLog,
    CandidateStatusHistory,
)
from apps.criteria.models import Criterion, HardStop
from apps.events.models import AIProviderLog, Event, EventCriterionScore
from apps.reports.models import ReportLog
from apps.users.models import User, UserProfile, UserTokenLimit
from core.choices import AttachmentType

fake = Faker("ru_RU")


class Command(BaseCommand):
    """
    Заполняет БД случайными тестовыми данными.
    Автоматически вызывает seed если базовых данных нет.
    Только для dev окружения.
    """

    help = "Заполнить БД случайными тестовыми данными (только dev)"

    def handle(self, *args, **options):
        self.stdout.write("Начинаем заполнение БД тестовыми данными...")

        self._ensure_seed_data()
        users = self._create_users(options["users"])
        self._create_candidates(
            users, options["candidates"], options["events"]
        )

        self.stdout.write(self.style.SUCCESS("БД успешно заполнена!"))

    def _ensure_seed_data(self) -> None:
        """Запускает seed если базовых данных ещё нет."""
        if not HardStop.objects.filter(is_default=True).exists():
            self.stdout.write(
                "  → Базовые данные не найдены, запускаем seed..."
            )
            from django.core.management import call_command

            call_command("seed", verbosity=0)

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=3,
            help="Количество пользователей (default: 3)",
        )
        parser.add_argument(
            "--candidates",
            type=int,
            default=3,
            help="Количество кандидатов на пользователя (default: 3)",
        )
        parser.add_argument(
            "--events",
            type=int,
            default=5,
            help="Количество событий на кандидата (default: 5)",
        )

    def _create_users(self, count: int) -> list[User]:
        """Создаёт тестовых пользователей с профилями и лимитами."""
        self.stdout.write(f"  → Пользователи ({count} шт.)...")

        users = []
        attachment_types = [
            AttachmentType.SECURE,
            AttachmentType.ANXIOUS,
            AttachmentType.AVOIDANT,
        ]
        for _ in range(count):
            telegram_id = random.randint(100_000_000, 999_999_999)
            user = User.objects.create_user(
                telegram_id=telegram_id,
                username=fake.user_name(),
            )
            UserProfile.objects.create(
                user=user,
                attachment_type=random.choice(attachment_types),
                attachment_source=UserProfile.AttachmentSource.BOT_TEST,
                correction_coefficient=round(random.uniform(0.8, 1.2), 2),
            )
            UserTokenLimit.objects.create(
                user=user,
                tier=UserTokenLimit.Tier.FREE,
                daily_limit=10_000,
                monthly_limit=100_000,
            )
            users.append(user)

        return users

    def _create_candidates(
        self,
        users: list[User],
        candidates_count: int,
        events_count: int,
    ) -> None:
        """Создаёт кандидатов с событиями для каждого пользователя."""
        criteria = list(Criterion.objects.filter(is_default=True))
        hard_stops = list(HardStop.objects.filter(is_default=True))
        test = AttachmentTest.objects.filter(is_active=True).first()

        for user in users:
            self.stdout.write(f"  → Кандидаты для {user}...")

            for _ in range(candidates_count):
                candidate = Candidate.objects.create(
                    user=user,
                    name=fake.first_name_female(),
                    age=random.randint(21, 35),
                    met_at=random.choice(
                        [
                            "Приложение для знакомств",
                            "Общие друзья",
                            "На работе",
                            "На мероприятии",
                        ]
                    ),
                    is_active=random.choice([True, True, True, False]),
                    ai_attachment_type=random.choice(
                        [
                            AttachmentType.SECURE,
                            AttachmentType.ANXIOUS,
                            AttachmentType.AVOIDANT,
                        ]
                    ),
                )

                # История статусов
                statuses = [
                    CandidateStatusHistory.Status.MEETING,
                    CandidateStatusHistory.Status.DATING,
                ]
                for status in statuses:
                    CandidateStatusHistory.objects.create(
                        candidate=candidate,
                        status=status,
                        note=fake.sentence(),
                    )

                # Hard Stop лог (иногда)
                if random.random() < 0.3:
                    hard_stop = random.choice(hard_stops)
                    CandidateHardStopLog.objects.create(
                        candidate=candidate,
                        hard_stop=hard_stop,
                        note=fake.sentence(),
                    )
                    candidate.hard_stop_triggered = True
                    candidate.save(update_fields=["hard_stop_triggered"])

                # Сессия теста для кандидата
                if test:
                    session = UserTestSession.objects.create(
                        user=user,
                        test=test,
                        result_type=random.choice(
                            [
                                AttachmentType.SECURE,
                                AttachmentType.ANXIOUS,
                                AttachmentType.AVOIDANT,
                            ]
                        ),
                    )
                    for question in test.questions.all():
                        UserAnswer.objects.create(
                            session=session,
                            question=question,
                            answer=random.randint(1, 5),
                        )

                # События
                self._create_events(candidate, criteria, events_count)

    def _create_events(
        self,
        candidate: Candidate,
        criteria: list[Criterion],
        count: int,
    ) -> None:
        """Создаёт события с оценками по критериям для кандидата."""
        raw_texts = [
            "Обещала позвонить в 8, позвонила в 10 без объяснений",
            "Сама спросила как прошёл мой день",
            "Призналась в ошибке первой без давления",
            "Опоздала на час без предупреждения",
            "Вспомнила о важном для меня событии",
            "Солгала про встречу с подругой",
            "Внимательно выслушала мою проблему",
            "Нагрубила без причины",
        ]
        for _ in range(count):
            event = Event.objects.create(
                candidate=candidate,
                raw_text=random.choice(raw_texts),
                ai_interpretation=fake.sentence(),
                is_hard_stop=random.random() < 0.1,
                bias_warning=fake.sentence() if random.random() < 0.2 else "",
            )

            # Оценки по 1-2 критериям
            selected_criteria = random.sample(criteria, k=random.randint(1, 2))
            for criterion in selected_criteria:
                ai_score = random.randint(-2, 2)
                EventCriterionScore.objects.create(
                    event=event,
                    criterion=criterion,
                    ai_score=ai_score,
                    user_score=(
                        ai_score + random.randint(-1, 1)
                        if random.random() < 0.3
                        else None
                    ),
                    is_confirmed=random.choice([True, False]),
                )

            # Лог AI провайдера
            AIProviderLog.objects.create(
                event=event,
                provider=AIProviderLog.Provider.CLAUDE,
                prompt=f"Проанализируй событие: {event.raw_text}",
                response=event.ai_interpretation,
                tokens_used=random.randint(100, 1000),
            )

            # Отчёт (иногда)
            if random.random() < 0.2:
                ReportLog.objects.create(
                    user=candidate.user,
                    candidate=candidate,
                    report_type=random.choice(
                        [
                            ReportLog.ReportType.TEXT,
                            ReportLog.ReportType.PDF,
                        ]
                    ),
                    trigger=ReportLog.Trigger.MANUAL,
                )

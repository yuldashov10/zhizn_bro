import random

from django.core.management.base import BaseCommand
from faker import Faker

from apps.assessments.models import (
    AttachmentTest,
    Question,
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

fake = Faker("ru_RU")


class Command(BaseCommand):
    """
    Заполняет БД случайными тестовыми данными.
    Создаёт пользователей, кандидатов, события и всё связанное.
    """

    help = "Заполнить БД тестовыми данными"

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

    def handle(self, *args, **options):
        self.stdout.write("Начинаем заполнение БД...")

        self._create_system_data()
        users = self._create_users(options["users"])
        self._create_candidates(
            users, options["candidates"], options["events"]
        )

        self.stdout.write(self.style.SUCCESS("БД успешно заполнена!"))

    def _create_system_data(self) -> None:
        """Создаёт системные Hard Stops и критерии."""
        self.stdout.write("  → Системные данные...")

        hard_stops = [
            (
                "Ложь / обман",
                "Нулевая терпимость. Любой зафиксированный обман — выход.",
            ),
            ("Разведена с детьми", "Наличие детей от предыдущих отношений."),
            ("Разведена без детей", "Был официальный брак без детей."),
            ("Курение", "Абсолютный маркер несовместимости."),
            (
                "Алкоголь / психотропные вещества",
                "Любое систематическое употребление.",
            ),
            ("Эзотерика / астрология", "Маркер отключённой Системы 2."),
            (
                "Дезорганизованный тип привязанности",
                "Неуправляемый шум в отношениях.",
            ),
        ]
        for name, description in hard_stops:
            HardStop.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "is_default": True,
                    "is_active": True,
                },
            )

        criteria = [
            (
                "Доверие",
                0.30,
                "Честность, выполнение обещаний, отсутствие лжи",
            ),
            (
                "Эмоц. стабильность",
                0.25,
                "Адекватность реакций, отсутствие манипуляций",
            ),
            (
                "Уважение",
                0.20,
                "Отношение к времени, мнению, границам партнёра",
            ),
            (
                "Открытость",
                0.15,
                "Готовность к серьёзным разговорам, честность о себе",
            ),
            ("Интеллект", 0.10, "Критическое мышление, адекватность суждений"),
        ]
        for name, weight, description in criteria:
            Criterion.objects.get_or_create(
                name=name,
                defaults={
                    "weight": weight,
                    "description": description,
                    "is_default": True,
                    "is_active": True,
                },
            )

        # Тест привязанности
        test, _ = AttachmentTest.objects.get_or_create(
            name="Краткий тест привязанности",
            defaults={
                "description": (
                    "Краткий тест для " "определения типа привязанности"
                ),
                "is_validated": False,
                "is_active": True,
            },
        )
        questions = [
            ("Мне легко сближаться с людьми", "anxiety"),
            ("Я беспокоюсь что партнёр меня бросит", "anxiety"),
            ("Я предпочитаю не зависеть от других", "avoidance"),
            ("Мне некомфортно когда партнёр слишком близко", "avoidance"),
            ("Я легко доверяю партнёру", "anxiety"),
        ]
        for i, (text, dimension) in enumerate(questions, 1):
            Question.objects.get_or_create(
                test=test,
                order=i,
                defaults={
                    "text": text,
                    "dimension": dimension,
                    "weight": 1.0,
                },
            )
        test.questions_count = test.questions.count()
        test.save(update_fields=["questions_count"])

    def _create_users(self, count: int) -> list[User]:
        """Создаёт тестовых пользователей с профилями и лимитами."""
        self.stdout.write(f"  → Пользователи ({count} шт.)...")

        users = []
        attachment_types = [
            UserProfile.AttachmentType.SECURE,
            UserProfile.AttachmentType.ANXIOUS,
            UserProfile.AttachmentType.AVOIDANT,
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
                            Candidate.AttachmentType.SECURE,
                            Candidate.AttachmentType.ANXIOUS,
                            Candidate.AttachmentType.AVOIDANT,
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
                                UserTestSession.AttachmentResult.SECURE,
                                UserTestSession.AttachmentResult.ANXIOUS,
                                UserTestSession.AttachmentResult.AVOIDANT,
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

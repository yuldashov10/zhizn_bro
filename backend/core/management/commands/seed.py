from django.core.management.base import BaseCommand

from apps.assessments.models import AttachmentTest, Question
from apps.criteria.models import Criterion, HardStop

HARD_STOPS = (
    (
        "Зафиксирована ложь / обман",
        (
            "Нулевая терпимость. Любой подтверждённый "
            "факт обмана — немедленный выход."
        ),
    ),
    (
        "Был развод (есть дети)",
        (
            "Наличие детей от предыдущих отношений. "
            "Высокий уровень внешних обязательств."
        ),
    ),
    (
        "Был развод (без детей)",
        "Опыт официального брака и развода без детей.",
    ),
    (
        "Активное курение",
        "Курит в настоящее время. Абсолютный маркер несовместимости.",
    ),
    (
        "Систематическое употребление алкоголя / ПАВ",
        "Регулярное употребление алкоголя или психоактивных веществ.",
    ),
    (
        "Вера в астрологию / эзотерику",
        (
            "Принятие решений на основе эзотерики. "
            "Маркер отключённого критического мышления."
        ),
    ),
    (
        "Дезорганизованный тип привязанности",
        (
            "Подтверждён тестом или паттерном поведения. "
            "Высокий уровень непредсказуемости в отношениях."
        ),
    ),
)

CRITERIA = (
    (
        "Доверие",
        0.30,
        "Честность, выполнение обещаний, отсутствие лжи и скрытых мотивов.",
    ),
    (
        "Эмоциональная стабильность",
        0.25,
        (
            "Адекватность реакций, отсутствие манипуляций "
            "и эмоциональных качелей."
        ),
    ),
    (
        "Уважение",
        0.20,
        "Отношение к времени, мнению и личным границам партнёра.",
    ),
    (
        "Открытость",
        0.15,
        "Готовность к честным разговорам о себе, своих планах и прошлом.",
    ),
    (
        "Критическое мышление",
        0.10,
        (
            "Способность к анализу, адекватность суждений, "
            "отсутствие магического мышления."
        ),
    ),
)

ATTACHMENT_TEST = {
    "name": "Краткий тест привязанности",
    "description": "Краткий тест для определения типа привязанности",
    "is_validated": False,
    "is_active": True,
}

QUESTIONS = (
    ("Мне легко сближаться с людьми", "anxiety", 1),
    ("Я беспокоюсь, что партнёр меня бросит", "anxiety", 2),
    ("Я предпочитаю не зависеть от других", "avoidance", 3),
    ("Мне некомфортно, когда партнёр слишком близко", "avoidance", 4),
    ("Я легко доверяю партнёру", "anxiety", 5),
)


class Command(BaseCommand):
    """
    Заполняет БД базовыми (seed) данными.
    Идемпотентна — безопасно запускать повторно.
    """

    help = (
        "Загрузить базовые данные (hard stops, критерии, тест привязанности)"
    )

    def handle(self, *args, **options) -> None:
        self.stdout.write("Загрузка базовых данных...")

        self._seed_hard_stops()
        self._seed_criteria()
        self._seed_attachment_test()

        self.stdout.write(
            self.style.SUCCESS("Базовые данные успешно загружены!")
        )

    def _seed_hard_stops(self) -> None:
        created_count = 0
        updated_count = 0

        for name, description in HARD_STOPS:
            _, created = HardStop.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "is_default": True,
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Hard Stops: {created_count} создано, {updated_count} обновлено"
        )

    def _seed_criteria(self) -> None:
        created_count = 0
        updated_count = 0

        for name, weight, description in CRITERIA:
            _, created = Criterion.objects.update_or_create(
                name=name,
                defaults={
                    "weight": weight,
                    "description": description,
                    "is_default": True,
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Критерии: {created_count} создано, {updated_count} обновлено"
        )

    def _seed_attachment_test(self) -> None:
        test, created = AttachmentTest.objects.update_or_create(
            name=ATTACHMENT_TEST["name"],
            defaults={
                "description": ATTACHMENT_TEST["description"],
                "is_validated": ATTACHMENT_TEST["is_validated"],
                "is_active": ATTACHMENT_TEST["is_active"],
            },
        )

        questions_created = 0
        questions_updated = 0

        for text, dimension, order in QUESTIONS:
            _, created_q = Question.objects.update_or_create(
                test=test,
                order=order,
                defaults={
                    "text": text,
                    "dimension": dimension,
                    "weight": 1.0,
                },
            )
            if created_q:
                questions_created += 1
            else:
                questions_updated += 1

        test.questions_count = test.questions.count()
        test.save(update_fields=["questions_count"])

        status = "создан" if created else "обновлён"
        self.stdout.write(
            f"  Тест привязанности: {status} "
            f"({questions_created} вопросов создано, "
            f"{questions_updated} обновлено)"
        )

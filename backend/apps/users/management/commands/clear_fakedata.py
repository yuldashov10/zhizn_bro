from django.core.management.base import BaseCommand

from apps.assessments.models import AttachmentTest, UserTestSession
from apps.candidates.models import Candidate
from apps.criteria.models import Criterion, HardStop
from apps.events.models import AIProviderLog, Event
from apps.reports.models import ReportLog
from apps.users.models import User


class Command(BaseCommand):
    """
    Полностью очищает БД от тестовых данных.
    Суперпользователи не удаляются.
    """

    help = "Очистить БД от тестовых данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Подтвердить очистку без интерактивного запроса",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            confirm = input(
                "Вы уверены что хотите очистить БД? "
                "Суперпользователи сохранятся. [y/N]: "
            )
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("Отменено."))
                return

        self.stdout.write("Начинаем очистку БД...")

        counts = {
            "Логи отчётов": ReportLog.objects.all().delete()[0],
            "Логи AI": AIProviderLog.objects.all().delete()[0],
            "События": Event.objects.all().delete()[0],
            "Кандидаты": Candidate.objects.all().delete()[0],
            "Сессии тестов": UserTestSession.objects.all().delete()[0],
            "Тесты": AttachmentTest.objects.all().delete()[0],
            "Критерии": Criterion.objects.all().delete()[0],
            "Hard Stops": HardStop.objects.all().delete()[0],
            "Пользователи": User.objects.filter(is_superuser=False).delete()[
                0
            ],
        }

        for name, count in counts.items():
            if count:
                self.stdout.write(f"  → Удалено {name}: {count}")

        self.stdout.write(self.style.SUCCESS("БД успешно очищена!"))

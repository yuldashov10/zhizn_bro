from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Аутентификация через Telegram ID вместо username/password.
    """

    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name="Telegram ID",
    )
    username = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Имя пользователя",
    )
    language = models.CharField(
        max_length=8,
        default="ru",
        verbose_name="Язык интерфейса",
    )

    first_name = None
    last_name = None
    email = None

    USERNAME_FIELD = "telegram_id"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return (
            f"@{self.username}" if self.username else f"tg:{self.telegram_id}"
        )


class UserProfile(models.Model):
    """
    Психологический профиль пользователя.
    Хранит тип привязанности и поправочный коэффициент для скоринга.
    """

    class AttachmentType(models.TextChoices):
        SECURE = "secure", "Надёжный"
        ANXIOUS = "anxious", "Тревожный"
        AVOIDANT = "avoidant", "Избегающий"
        DISORGANIZED = "disorganized", "Дезорганизованный"

    class AttachmentSource(models.TextChoices):
        BOT_TEST = "bot_test", "Тест в боте"
        USER_DEFINED = "user_defined", "Указан вручную"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    attachment_type = models.CharField(
        max_length=20,
        choices=AttachmentType.choices,
        blank=True,
        null=True,
        verbose_name="Тип привязанности",
    )
    attachment_source = models.CharField(
        max_length=20,
        choices=AttachmentSource.choices,
        blank=True,
        null=True,
        verbose_name="Источник типа привязанности",
    )
    correction_coefficient = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(1.5)],
        verbose_name="Поправочный коэффициент скоринга",
    )

    test_session = models.ForeignKey(
        "assessments.UserTestSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles",
        verbose_name="Сессия теста",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self) -> str:
        return f"Профиль {self.user}"


class UserTokenLimit(models.Model):
    """
    Лимиты использования токенов ИИ для пользователя.
    Сбрасывается ежедневно и ежемесячно через Celery.
    """

    class Tier(models.TextChoices):
        FREE = "free", "Бесплатный"
        PRO = "pro", "Pro"
        TRIAL = "trial", "Пробный"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="token_limit",
        verbose_name="Пользователь",
    )
    daily_limit = models.IntegerField(
        default=10_000,
        verbose_name="Дневной лимит токенов",
    )
    monthly_limit = models.IntegerField(
        default=100_000,
        verbose_name="Месячный лимит токенов",
    )
    used_today = models.IntegerField(
        default=0,
        verbose_name="Использовано сегодня",
    )
    used_this_month = models.IntegerField(
        default=0,
        verbose_name="Использовано в этом месяце",
    )
    tier = models.CharField(
        max_length=20,
        choices=Tier.choices,
        default=Tier.FREE,
        verbose_name="Тариф",
    )
    reset_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время следующего сброса",
    )

    class Meta:
        verbose_name = "Лимит токенов"
        verbose_name_plural = "Лимиты токенов"

    def __str__(self) -> str:
        return f"Лимиты {self.user} [{self.tier}]"

    def is_daily_limit_exceeded(self) -> bool:
        """Проверяет превышение дневного лимита."""
        return self.used_today >= self.daily_limit

    def is_monthly_limit_exceeded(self) -> bool:
        """Проверяет превышение месячного лимита."""
        return self.used_this_month >= self.monthly_limit

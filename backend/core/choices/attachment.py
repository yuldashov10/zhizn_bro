from django.db import models


class AttachmentType(models.TextChoices):
    """Тип привязанности — используется в профиле, кандидате и тесте."""

    SECURE = "secure", "Надёжный"
    ANXIOUS = "anxious", "Тревожный"
    AVOIDANT = "avoidant", "Избегающий"
    DISORGANIZED = "disorganized", "Дезорганизованный"

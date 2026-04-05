from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
    Кастомный менеджер пользователя.
    Аутентификация через Telegram ID без пароля.
    """

    def create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        **extra_fields,
    ):
        """Создаёт и сохраняет обычного пользователя."""
        if not telegram_id:
            raise ValueError("Telegram ID обязателен")

        user = self.model(
            telegram_id=telegram_id,
            username=username,
            **extra_fields,
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        telegram_id: int,
        username: str | None = None,
        password: str | None = None,
        **extra_fields,
    ):
        """Создаёт и сохраняет суперпользователя."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError(
                "Суперпользователь должен иметь is_superuser=True"
            )

        user = self.model(
            telegram_id=telegram_id,
            username=username,
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

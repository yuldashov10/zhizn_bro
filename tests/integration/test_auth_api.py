from apps.users.models import User, UserProfile, UserTokenLimit


class TestTelegramAuth:
    """Тесты аутентификации через Telegram."""

    def test_new_user_registration(self, db, anon_client):
        """Новый пользователь регистрируется и получает токен."""
        response = anon_client.post(
            "/api/v1/auth/telegram/",
            {
                "telegram_id": 123456789,
                "username": "test_user",
            },
        )
        assert response.status_code == 201
        assert "token" in response.data
        assert response.data["created"] is True

    def test_existing_user_login(self, db, anon_client, user):
        """Существующий пользователь получает токен."""
        response = anon_client.post(
            "/api/v1/auth/telegram/",
            {
                "telegram_id": user.telegram_id,
            },
        )
        assert response.status_code == 200
        assert response.data["created"] is False

    def test_new_user_profile_created(self, db, anon_client):
        """При регистрации создаётся профиль и лимиты токенов."""
        anon_client.post(
            "/api/v1/auth/telegram/",
            {
                "telegram_id": 987654321,
            },
        )
        user = User.objects.get(telegram_id=987654321)
        assert UserProfile.objects.filter(user=user).exists()
        assert UserTokenLimit.objects.filter(user=user).exists()

    def test_invalid_telegram_id(self, db, anon_client):
        """Невалидный telegram_id возвращает 400."""
        response = anon_client.post(
            "/api/v1/auth/telegram/",
            {
                "telegram_id": -1,
            },
        )
        assert response.status_code == 400

    def test_username_updated_on_login(self, db, anon_client, user):
        """Username обновляется при повторном входе."""
        anon_client.post(
            "/api/v1/auth/telegram/",
            {
                "telegram_id": user.telegram_id,
                "username": "new_username",
            },
        )
        user.refresh_from_db()
        assert user.username == "new_username"

    def test_token_is_consistent(self, db, anon_client, user):
        """Повторный вход возвращает тот же токен."""
        r1 = anon_client.post(
            "/api/v1/auth/telegram/",
            {
                "telegram_id": user.telegram_id,
            },
        )
        r2 = anon_client.post(
            "/api/v1/auth/telegram/",
            {
                "telegram_id": user.telegram_id,
            },
        )
        assert r1.data["token"] == r2.data["token"]

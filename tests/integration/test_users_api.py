class TestMeEndpoint:
    """Тесты эндпоинта профиля пользователя."""

    def test_get_profile(self, api_client, user):
        response = api_client.get("/api/v1/users/me/")
        assert response.status_code == 200
        assert response.data["telegram_id"] == user.telegram_id

    def test_unauthenticated_returns_401(self, anon_client):
        response = anon_client.get("/api/v1/users/me/")
        assert response.status_code == 401

    def test_update_language(self, api_client, user):
        response = api_client.patch("/api/v1/users/me/", {"language": "en"})
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.language == "en"

    def test_update_attachment_type(self, api_client, user):
        response = api_client.patch(
            "/api/v1/users/me/",
            {
                "attachment_type": "anxious",
                "attachment_source": "user_defined",
            },
        )
        assert response.status_code == 200
        user.profile.refresh_from_db()
        assert user.profile.attachment_type == "anxious"

    def test_profile_contains_token_limit(self, api_client, user):
        response = api_client.get("/api/v1/users/me/")
        assert "profile" in response.data
        assert "token_limit" in response.data

    def test_token_limit_endpoint(self, api_client, user):
        response = api_client.get("/api/v1/users/me/token-limit/")
        assert response.status_code == 200
        assert "daily_limit" in response.data
        assert "used_today" in response.data

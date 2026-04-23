from apps.criteria.models import HardStopSuggestion


class TestHardStopList:
    def test_get_system_hard_stops(self, api_client, system_hard_stops):
        response = api_client.get("/api/v1/hard-stops/")
        assert response.status_code == 200
        assert len(response.data) == len(system_hard_stops)

    def test_unauthenticated_returns_401(self, anon_client):
        response = anon_client.get("/api/v1/hard-stops/")
        assert response.status_code == 401


class TestHardStopToggle:
    def test_toggle_hard_stop(self, api_client, system_hard_stops):
        hs = system_hard_stops[0]
        response = api_client.post(f"/api/v1/hard-stops/{hs.pk}/toggle/")
        assert response.status_code == 200
        assert response.data["is_active"] is False

    def test_toggle_is_per_user(
        self, api_client, another_client, system_hard_stops
    ):
        """Настройки Hard Stop независимы для каждого пользователя."""
        hs = system_hard_stops[0]
        api_client.post(f"/api/v1/hard-stops/{hs.pk}/toggle/")

        # У другого пользователя Hard Stop всё ещё активен
        response = another_client.get("/api/v1/hard-stops/")
        hs_data = next(h for h in response.data if h["id"] == hs.pk)
        assert hs_data["is_active"] is True


class TestHardStopSuggest:
    def test_suggest_hard_stop(self, api_client):
        response = api_client.post(
            "/api/v1/hard-stops/suggest/",
            {
                "text": "Наличие серьёзных долгов",
            },
        )
        assert response.status_code == 201
        assert response.data["status"] == "pending"

    def test_suggest_too_short(self, api_client):
        response = api_client.post(
            "/api/v1/hard-stops/suggest/",
            {
                "text": "Коротко",
            },
        )
        assert response.status_code == 400

    def test_suggestion_saved(self, api_client, user):
        api_client.post(
            "/api/v1/hard-stops/suggest/",
            {
                "text": "Систематическое враньё близким",
            },
        )
        assert HardStopSuggestion.objects.filter(user=user).count() == 1

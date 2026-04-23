from tests.factories import CandidateFactory


class TestCandidateList:
    """Тесты списка кандидатов."""

    def test_get_empty_list(self, api_client):
        response = api_client.get("/api/v1/candidates/")
        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_get_own_candidates(self, api_client, user):
        CandidateFactory.create_batch(3, user=user)
        response = api_client.get("/api/v1/candidates/")
        assert response.data["count"] == 3

    def test_cannot_see_other_users_candidates(self, api_client, another_user):
        """Пользователь не видит чужих кандидатов."""
        CandidateFactory.create_batch(2, user=another_user)
        response = api_client.get("/api/v1/candidates/")
        assert response.data["count"] == 0

    def test_create_candidate(self, api_client):
        response = api_client.post(
            "/api/v1/candidates/",
            {
                "name": "Тест",
                "age": 25,
                "met_at": "На улице",
            },
        )
        assert response.status_code == 201
        assert response.data["name"] == "Тест"

    def test_filter_by_is_active(self, api_client, user):
        CandidateFactory(user=user, is_active=True)
        CandidateFactory(user=user, is_active=False)
        response = api_client.get("/api/v1/candidates/?is_active=true")
        assert response.data["count"] == 1


class TestCandidateDetail:
    """Тесты детальной информации о кандидате."""

    def test_get_own_candidate(self, api_client, user):
        candidate = CandidateFactory(user=user)
        response = api_client.get(f"/api/v1/candidates/{candidate.pk}/")
        assert response.status_code == 200
        assert response.data["name"] == candidate.name

    def test_cannot_get_other_candidate(self, api_client, another_user):
        """Нельзя получить чужого кандидата."""
        candidate = CandidateFactory(user=another_user)
        response = api_client.get(f"/api/v1/candidates/{candidate.pk}/")
        assert response.status_code == 404

    def test_archive_candidate(self, api_client, user):
        candidate = CandidateFactory(user=user)
        response = api_client.post(
            f"/api/v1/candidates/{candidate.pk}/archive/"
        )
        assert response.status_code == 200
        candidate.refresh_from_db()
        assert candidate.is_active is False

    def test_archive_already_archived(self, api_client, user):
        candidate = CandidateFactory(user=user, is_active=False)
        response = api_client.post(
            f"/api/v1/candidates/{candidate.pk}/archive/"
        )
        assert response.status_code == 400

    def test_get_score_no_events(self, api_client, user):
        candidate = CandidateFactory(user=user)
        response = api_client.get(f"/api/v1/candidates/{candidate.pk}/score/")
        assert response.status_code == 200
        assert response.data["score"] is None

    def test_update_status(self, api_client, user):
        candidate = CandidateFactory(user=user)
        response = api_client.post(
            f"/api/v1/candidates/{candidate.pk}/status/",
            {"status": "dating", "note": "Начали встречаться"},
        )
        assert response.status_code == 201
        assert candidate.status_history.count() == 1

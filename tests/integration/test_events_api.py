from unittest.mock import patch

from tests.factories import CandidateFactory, CriterionFactory, EventFactory


class TestEventList:
    """Тесты списка событий."""

    def test_requires_candidate_param(self, api_client):
        response = api_client.get("/api/v1/events/")
        assert response.status_code == 400

    def test_get_events_for_candidate(self, api_client, user):
        candidate = CandidateFactory(user=user)
        EventFactory.create_batch(3, candidate=candidate)
        response = api_client.get(f"/api/v1/events/?candidate={candidate.pk}")
        assert response.data["count"] == 3

    def test_cannot_get_other_candidate_events(self, api_client, another_user):
        """Нельзя получить события чужого кандидата."""
        candidate = CandidateFactory(user=another_user)
        EventFactory(candidate=candidate)
        response = api_client.get(f"/api/v1/events/?candidate={candidate.pk}")
        assert response.status_code == 404

    def test_filter_by_is_hard_stop(self, api_client, user):
        candidate = CandidateFactory(user=user)
        EventFactory(candidate=candidate, is_hard_stop=True)
        EventFactory(candidate=candidate, is_hard_stop=False)
        response = api_client.get(
            f"/api/v1/events/?candidate={candidate.pk}&is_hard_stop=true"
        )
        assert response.data["count"] == 1


class TestEventCreate:
    """Тесты создания событий."""

    def test_create_event_calls_ai(self, api_client, user):
        """Создание события запускает AI анализ."""
        candidate = CandidateFactory(user=user)
        with patch(
            "api.v1.events.views.AIAnalysisService.analyze"
        ) as mock_analyze:
            mock_analyze.return_value = None
            response = api_client.post(
                "/api/v1/events/",
                {
                    "candidate": candidate.pk,
                    "raw_text": "Опоздала на встречу без предупреждения",
                },
            )
        assert response.status_code == 201
        mock_analyze.assert_called_once()

    def test_create_event_too_short_text(self, api_client, user):
        candidate = CandidateFactory(user=user)
        response = api_client.post(
            "/api/v1/events/",
            {
                "candidate": candidate.pk,
                "raw_text": "Коротко",
            },
        )
        assert response.status_code == 400

    def test_cannot_create_event_for_other_candidate(
        self, api_client, another_user
    ):
        candidate = CandidateFactory(user=another_user)
        response = api_client.post(
            "/api/v1/events/",
            {
                "candidate": candidate.pk,
                "raw_text": "Тестовое событие для проверки",
            },
        )
        assert response.status_code == 404


class TestEventConfirm:
    """Тесты подтверждения оценки ИИ."""

    def test_confirm_score(self, api_client, user):
        candidate = CandidateFactory(user=user)
        criterion = CriterionFactory()
        event = EventFactory(candidate=candidate)
        from apps.events.models import EventCriterionScore

        score = EventCriterionScore.objects.create(
            event=event,
            criterion=criterion,
            ai_score=-1,
        )
        response = api_client.patch(
            f"/api/v1/events/{event.pk}/confirm/",
            {"criterion": criterion.pk, "is_confirmed": True},
        )
        assert response.status_code == 200
        score.refresh_from_db()
        assert score.is_confirmed is True

    def test_correct_ai_score(self, api_client, user):
        """Пользователь корректирует оценку ИИ."""
        candidate = CandidateFactory(user=user)
        criterion = CriterionFactory()
        event = EventFactory(candidate=candidate)
        from apps.events.models import EventCriterionScore

        score = EventCriterionScore.objects.create(
            event=event,
            criterion=criterion,
            ai_score=-2,
        )
        response = api_client.patch(
            f"/api/v1/events/{event.pk}/confirm/",
            {
                "criterion": criterion.pk,
                "user_score": -1,
                "is_confirmed": True,
            },
        )
        assert response.status_code == 200
        score.refresh_from_db()
        assert score.user_score == -1
        assert score.final_score == -1

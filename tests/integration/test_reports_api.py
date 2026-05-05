from unittest.mock import patch

from tests.factories import CandidateFactory, EventFactory


class TestReportGenerate:
    """Тесты генерации отчётов."""

    def test_generate_text_report(self, api_client, user):
        candidate = CandidateFactory(user=user)
        EventFactory(candidate=candidate)
        with patch(
            "api.v1.reports.views.ReportService.generate_text_report"
        ) as mock:
            mock.return_value = "Текстовый отчёт"
            response = api_client.post(
                "/api/v1/reports/generate/",
                {
                    "report_type": "text",
                    "candidate_id": candidate.pk,
                },
            )
        assert response.status_code == 201
        assert "text" in response.data

    def test_cannot_generate_report_no_events(self, api_client, user):
        """Нельзя генерировать отчёт без событий."""
        candidate = CandidateFactory(user=user)
        response = api_client.post(
            "/api/v1/reports/generate/",
            {
                "report_type": "pdf",
                "candidate_id": candidate.pk,
            },
        )
        assert response.status_code == 400

    def test_cannot_generate_report_for_other_candidate(
        self, api_client, another_user
    ):
        candidate = CandidateFactory(user=another_user)
        response = api_client.post(
            "/api/v1/reports/generate/",
            {
                "report_type": "text",
                "candidate_id": candidate.pk,
            },
        )
        assert response.status_code == 404

    def test_get_reports_list(self, api_client, user):
        from tests.factories import ReportLogFactory

        ReportLogFactory.create_batch(3, user=user)
        response = api_client.get("/api/v1/reports/")
        assert response.status_code == 200
        assert response.data["count"] == 3

    def test_cannot_see_other_users_reports(self, api_client, another_user):
        from tests.factories import ReportLogFactory

        ReportLogFactory.create_batch(2, user=another_user)
        response = api_client.get("/api/v1/reports/")
        assert response.data["count"] == 0

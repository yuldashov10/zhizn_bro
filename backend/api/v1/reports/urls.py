from api.v1.reports.views import ReportGenerateView, ReportListView
from django.urls import path

urlpatterns = [
    path("reports/", ReportListView.as_view(), name="reports-list"),
    path(
        "reports/generate/",
        ReportGenerateView.as_view(),
        name="reports-generate",
    ),
]

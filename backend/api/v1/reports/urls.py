from api.v1.reports.views import (
    ReportDetailView,
    ReportGenerateView,
    ReportListView,
)
from django.urls import path

urlpatterns = [
    path("reports/", ReportListView.as_view(), name="reports-list"),
    path(
        "reports/<int:pk>/", ReportDetailView.as_view(), name="reports-detail"
    ),
    path(
        "reports/generate/",
        ReportGenerateView.as_view(),
        name="reports-generate",
    ),
]

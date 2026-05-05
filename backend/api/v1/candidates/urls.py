from django.urls import path

from api.v1.candidates.views import (
    CandidateArchiveView,
    CandidateDetailView,
    CandidateListView,
    CandidateScoreView,
    CandidateStatusHistoryView,
    CandidateStatusUpdateView,
)

urlpatterns = [
    path("candidates/", CandidateListView.as_view(), name="candidates-list"),
    path(
        "candidates/<int:pk>/",
        CandidateDetailView.as_view(),
        name="candidates-detail",
    ),
    path(
        "candidates/<int:pk>/archive/",
        CandidateArchiveView.as_view(),
        name="candidates-archive",
    ),
    path(
        "candidates/<int:pk>/score/",
        CandidateScoreView.as_view(),
        name="candidates-score",
    ),
    path(
        "candidates/<int:pk>/status-history/",
        CandidateStatusHistoryView.as_view(),
        name="candidates-status-history",
    ),
    path(
        "candidates/<int:pk>/status/",
        CandidateStatusUpdateView.as_view(),
        name="candidates-status-update",
    ),
]

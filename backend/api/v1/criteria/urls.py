from api.v1.criteria.views import (
    CriterionDetailView,
    CriterionListView,
    HardStopDetailView,
    HardStopListView,
)
from django.urls import path

urlpatterns = [
    path("hard-stops/", HardStopListView.as_view(), name="hard-stops-list"),
    path(
        "hard-stops/<int:pk>/",
        HardStopDetailView.as_view(),
        name="hard-stops-detail",
    ),
    path("criteria/", CriterionListView.as_view(), name="criteria-list"),
    path(
        "criteria/<int:pk>/",
        CriterionDetailView.as_view(),
        name="criteria-detail",
    ),
]

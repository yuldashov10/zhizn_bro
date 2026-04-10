from django.urls import path

from api.v1.criteria.views import (
    CriterionDetailView,
    CriterionListView,
    CriterionToggleView,
    HardStopDetailView,
    HardStopListView,
    HardStopSuggestView,
    HardStopToggleView,
)

urlpatterns = [
    path("hard-stops/", HardStopListView.as_view(), name="hard-stops-list"),
    path(
        "hard-stops/<int:pk>/",
        HardStopDetailView.as_view(),
        name="hard-stops-detail",
    ),
    path(
        "hard-stops/<int:pk>/toggle/",
        HardStopToggleView.as_view(),
        name="hard-stops-toggle",
    ),
    path(
        "hard-stops/suggest/",
        HardStopSuggestView.as_view(),
        name="hard-stops-suggest",
    ),
    path("criteria/", CriterionListView.as_view(), name="criteria-list"),
    path(
        "criteria/<int:pk>/",
        CriterionDetailView.as_view(),
        name="criteria-detail",
    ),
    path(
        "criteria/<int:pk>/toggle/",
        CriterionToggleView.as_view(),
        name="criteria-toggle",
    ),
]

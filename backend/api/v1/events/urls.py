from django.urls import path

from api.v1.events.views import (
    EventConfirmView,
    EventDetailView,
    EventListView,
)

urlpatterns = [
    path("events/", EventListView.as_view(), name="events-list"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="events-detail"),
    path(
        "events/<int:pk>/confirm/",
        EventConfirmView.as_view(),
        name="events-confirm",
    ),
]

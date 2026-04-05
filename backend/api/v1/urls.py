from django.urls import include, path

urlpatterns = [
    path("", include("api.v1.users.urls")),
    path("", include("api.v1.assessments.urls")),
    path("", include("api.v1.criteria.urls")),
    path("", include("api.v1.candidates.urls")),
    path("", include("api.v1.events.urls")),
    path("", include("api.v1.reports.urls")),
]

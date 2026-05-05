from django.urls import path

from api.v1.assessments.views import (
    AttachmentTestDetailView,
    AttachmentTestListView,
    TestSessionAnswerView,
    TestSessionDetailView,
    TestSessionResultView,
    TestStartView,
)

urlpatterns = [
    path(
        "assessments/tests/",
        AttachmentTestListView.as_view(),
        name="assessments-list",
    ),
    path(
        "assessments/tests/<int:pk>/",
        AttachmentTestDetailView.as_view(),
        name="assessments-detail",
    ),
    path(
        "assessments/tests/<int:pk>/start/",
        TestStartView.as_view(),
        name="assessments-start",
    ),
    path(
        "assessments/sessions/<int:pk>/",
        TestSessionDetailView.as_view(),
        name="assessments-session-detail",
    ),
    path(
        "assessments/sessions/<int:pk>/answer/",
        TestSessionAnswerView.as_view(),
        name="assessments-session-answer",
    ),
    path(
        "assessments/sessions/<int:pk>/result/",
        TestSessionResultView.as_view(),
        name="assessments-session-result",
    ),
]

from django.urls import path

from api.v1.users.views import MeView, TelegramAuthView, TokenLimitView

urlpatterns = [
    path("auth/telegram/", TelegramAuthView.as_view(), name="auth-telegram"),
    path("users/me/", MeView.as_view(), name="users-me"),
    path(
        "users/me/token-limit/",
        TokenLimitView.as_view(),
        name="users-token-limit",
    ),
]

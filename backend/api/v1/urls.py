from decouple import config as env_config
from django.http import JsonResponse
from django.urls import include, path
from django.views import View


class HealthCheckView(View):
    """
    Health check эндпоинт для мониторинга доступности сервиса.
    Используется UptimeRobot и другими мониторинг сервисами.
    """

    def get(self, request):
        from django.db import connection

        try:
            # Проверяем доступность БД
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        status = "ok" if db_ok else "degraded"
        code = 200 if db_ok else 503

        return JsonResponse(
            {
                "status": status,
                "database": "ok" if db_ok else "error",
                "version": env_config("APP_VERSION", default="1.0.0"),
            },
            status=code,
        )


urlpatterns = [
    path("", include("api.v1.users.urls")),
    path("", include("api.v1.assessments.urls")),
    path("", include("api.v1.criteria.urls")),
    path("", include("api.v1.candidates.urls")),
    path("", include("api.v1.events.urls")),
    path("", include("api.v1.reports.urls")),
]

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from api.v1.urls import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.v1.urls")),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path(
        "", TemplateView.as_view(template_name="landing.html"), name="landing"
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

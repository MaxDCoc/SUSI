from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from accounts import views as auth_views
from catalog.views import CatalogosView, PracticaViewSet
from evidence.views import EvidenciaViewSet
from indicators.views import IndicadorViewSet, MedicionViewSet

from .views import health

router = SimpleRouter()
router.register("practicas", PracticaViewSet, basename="practica")
router.register("indicadores", IndicadorViewSet, basename="indicador")
router.register("mediciones", MedicionViewSet, basename="medicion")
router.register("evidencias", EvidenciaViewSet, basename="evidencia")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/auth/session/", auth_views.sesion, name="auth-sesion"),
    path("api/auth/login/", auth_views.login_view, name="auth-login"),
    path("api/auth/logout/", auth_views.logout_view, name="auth-logout"),
    path("api/catalogos/", CatalogosView.as_view(), name="catalogos"),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/", include(router.urls)),
]

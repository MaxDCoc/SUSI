from django.urls import path

from .views import MuestrasView, ParametrosView, SCIView

urlpatterns = [
    path("sci/", SCIView.as_view(), name="green-sci"),
    path("muestras/", MuestrasView.as_view(), name="green-muestras"),
    path("parametros/", ParametrosView.as_view(), name="green-parametros"),
]

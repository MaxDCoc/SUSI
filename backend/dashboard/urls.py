from django.urls import path

from .views import EmbudoView, ResumenView

urlpatterns = [
    path("embudo/", EmbudoView.as_view(), name="dashboard-embudo"),
    path("resumen/", ResumenView.as_view(), name="dashboard-resumen"),
]

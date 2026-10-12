from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        from catalog.models import Facultad, Practica
        from evidence.models import Evidencia
        from indicators.models import Indicador, Medicion

        from .cache import invalidar

        for modelo in (Facultad, Practica, Indicador, Medicion, Evidencia):
            post_save.connect(invalidar, sender=modelo, dispatch_uid=f"dashboard-save-{modelo.__name__}")
            post_delete.connect(invalidar, sender=modelo, dispatch_uid=f"dashboard-delete-{modelo.__name__}")

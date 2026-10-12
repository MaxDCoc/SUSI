from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Evidencia


@admin.register(Evidencia)
class EvidenciaAdmin(SimpleHistoryAdmin):
    list_display = ("__str__", "tipo", "medicion", "practica", "creado_por", "creado_en")
    list_filter = ("tipo",)
    raw_id_fields = ("medicion", "practica", "creado_por")

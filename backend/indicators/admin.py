from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Indicador, Medicion


@admin.register(Indicador)
class IndicadorAdmin(SimpleHistoryAdmin):
    list_display = ("nombre", "practica", "unidad", "periodicidad", "tipo")
    list_filter = ("tipo", "periodicidad", "practica__facultad")
    search_fields = ("nombre", "practica__nombre")
    raw_id_fields = ("practica", "responsable_datos")


@admin.register(Medicion)
class MedicionAdmin(SimpleHistoryAdmin):
    list_display = ("indicador", "periodo", "valor", "estado", "cargado_por", "validado_por")
    list_filter = ("estado", "indicador__practica__facultad")
    raw_id_fields = ("indicador", "cargado_por")
    # El estado cambia solo por las reglas de workflow.
    readonly_fields = ("estado", "validado_por", "validado_en")

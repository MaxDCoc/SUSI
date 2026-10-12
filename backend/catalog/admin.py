from django.contrib import admin
from guardian.admin import GuardedModelAdminMixin
from simple_history.admin import SimpleHistoryAdmin

from .models import ODS, Facultad, Practica, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)


@admin.register(Facultad)
class FacultadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "region", "es_nivel_central")
    list_filter = ("region", "es_nivel_central")
    search_fields = ("nombre",)


@admin.register(ODS)
class ODSAdmin(admin.ModelAdmin):
    list_display = ("numero", "nombre")


@admin.register(Practica)
class PracticaAdmin(GuardedModelAdminMixin, SimpleHistoryAdmin):
    list_display = ("nombre", "facultad", "dimension", "estado", "origen")
    list_filter = ("estado", "dimension", "origen", "facultad__region")
    search_fields = ("nombre", "facultad__nombre")
    raw_id_fields = ("responsable",)
    filter_horizontal = ("ods",)
    # El estado solo cambia por las reglas de workflow (promover / retroceder).
    readonly_fields = ("estado",)

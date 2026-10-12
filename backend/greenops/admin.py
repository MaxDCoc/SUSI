from django.contrib import admin

from .models import MuestraOperacion, ParametroSCI


@admin.register(ParametroSCI)
class ParametroSCIAdmin(admin.ModelAdmin):
    list_display = ("version", "potencia_cpu_w", "intensidad_carbono_g_kwh", "fuente_intensidad", "fecha_intensidad")
    readonly_fields = ("version", "creado_en")


@admin.register(MuestraOperacion)
class MuestraOperacionAdmin(admin.ModelAdmin):
    list_display = ("operacion", "cpu_ms", "wall_ms", "bytes_respuesta", "n_consultas_sql", "ts")
    list_filter = ("operacion",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

from django.contrib import admin

from .models import Membership


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "facultad", "rol")
    list_filter = ("rol", "facultad__region")
    search_fields = ("user__username", "facultad__nombre")
    raw_id_fields = ("user",)

    def get_readonly_fields(self, request, obj=None):
        # Los permisos de objeto se sincronizan al crear/borrar la membresía: para cambiar rol o facultad, borrar y crear.
        return ("user", "facultad", "rol") if obj else ()

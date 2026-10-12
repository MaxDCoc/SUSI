from django.contrib import admin

from .models import Membership


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "facultad", "rol")
    list_filter = ("rol", "facultad__region")
    search_fields = ("user__username", "facultad__nombre")
    raw_id_fields = ("user",)

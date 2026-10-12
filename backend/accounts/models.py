from django.conf import settings
from django.db import models


class Rol(models.TextChoices):
    RESPONSABLE = "responsable", "Responsable"
    VALIDADOR = "validador", "Validador"


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membresias")
    facultad = models.ForeignKey("catalog.Facultad", on_delete=models.CASCADE, related_name="membresias")
    rol = models.CharField(max_length=20, choices=Rol.choices)

    class Meta:
        verbose_name = "membresía"
        verbose_name_plural = "membresías"
        constraints = [
            models.UniqueConstraint(fields=["user", "facultad", "rol"], name="uniq_membership"),
        ]

    def __str__(self):
        return f"{self.user} · {self.get_rol_display()} · {self.facultad}"

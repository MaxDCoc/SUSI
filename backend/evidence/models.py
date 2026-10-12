import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from .validators import validar_archivo


class TipoEvidencia(models.TextChoices):
    ARCHIVO = "archivo", "Archivo"
    ENLACE = "enlace", "Enlace"


def ruta_evidencia(instance, filename):
    extension = os.path.splitext(filename)[1].lower()
    return f"evidencias/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{extension}"


class Evidencia(models.Model):
    medicion = models.ForeignKey(
        "indicators.Medicion", null=True, blank=True, on_delete=models.CASCADE, related_name="evidencias"
    )
    practica = models.ForeignKey(
        "catalog.Practica", null=True, blank=True, on_delete=models.CASCADE, related_name="evidencias"
    )
    tipo = models.CharField(max_length=20, choices=TipoEvidencia.choices)
    archivo = models.FileField(upload_to=ruta_evidencia, blank=True, validators=[validar_archivo])
    url = models.URLField(blank=True, validators=[URLValidator(schemes=["http", "https"])])
    descripcion = models.CharField(max_length=200, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="evidencias_cargadas"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "evidencias"

    def __str__(self):
        return self.descripcion or f"Evidencia {self.pk}"

    def clean(self):
        if not self.medicion_id and not self.practica_id:
            raise ValidationError("La evidencia debe pertenecer a una medición o a una práctica.")
        if self.medicion_id and self.practica_id:
            if self.medicion.indicador.practica_id != self.practica_id:
                raise ValidationError("La medición no pertenece a la práctica indicada.")
        if self.tipo == TipoEvidencia.ARCHIVO and not self.archivo:
            raise ValidationError("Falta adjuntar el archivo.")
        if self.tipo == TipoEvidencia.ENLACE and not self.url:
            raise ValidationError("Falta indicar el enlace.")

    @property
    def facultad_scope_id(self) -> int:
        if self.medicion_id:
            return self.medicion.facultad_scope_id
        return self.practica.facultad_scope_id

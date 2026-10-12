from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max


class MuestraOperacion(models.Model):
    ts = models.DateTimeField(auto_now_add=True, db_index=True)
    operacion = models.CharField(max_length=60, db_index=True)
    cpu_ms = models.FloatField()
    wall_ms = models.FloatField()
    bytes_respuesta = models.PositiveIntegerField()
    n_consultas_sql = models.PositiveIntegerField()

    class Meta:
        verbose_name = "muestra de operación"
        verbose_name_plural = "muestras de operación"

    def __str__(self):
        return f"{self.operacion} ({self.wall_ms:.1f} ms)"


class ParametroSCI(models.Model):
    """Juego versionado de supuestos para estimar el SCI (ISO/IEC 21031:2024)."""

    version = models.PositiveIntegerField(unique=True, editable=False, null=True, blank=True)
    potencia_cpu_w = models.DecimalField(
        "potencia de CPU (W)", max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    intensidad_carbono_g_kwh = models.DecimalField(
        "intensidad de carbono (gCO2e/kWh)",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    fuente_intensidad = models.CharField("fuente de la intensidad de carbono", max_length=200)
    fecha_intensidad = models.DateField("fecha del dato de intensidad")
    te_g = models.DecimalField(
        "emisiones incorporadas totales TE (gCO2e)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    el_horas = models.DecimalField(
        "vida útil esperada EL (horas)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    rs = models.DecimalField(
        "recursos reservados RS", max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0"))]
    )
    tr = models.DecimalField(
        "recursos totales TR", max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))]
    )
    supuestos = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "parámetro SCI"
        verbose_name_plural = "parámetros SCI"
        ordering = ["-version"]

    def __str__(self):
        return f"Parámetros SCI v{self.version}"

    def save(self, *args, **kwargs):
        if self.version is None:
            self.version = (ParametroSCI.objects.aggregate(m=Max("version"))["m"] or 0) + 1
        super().save(*args, **kwargs)

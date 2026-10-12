from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from simple_history.models import HistoricalRecords


class Periodicidad(models.TextChoices):
    MENSUAL = "mensual", "Mensual"
    TRIMESTRAL = "trimestral", "Trimestral"
    SEMESTRAL = "semestral", "Semestral"
    ANUAL = "anual", "Anual"


class TipoIndicador(models.TextChoices):
    INSTITUCIONAL = "institucional", "Institucional"
    TECNICO = "tecnico", "Técnico"


class EstadoMedicion(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    ENVIADA = "enviada", "Enviada"
    VALIDADA = "validada", "Validada"
    RECHAZADA = "rechazada", "Rechazada"


# \Z (y no $) para no aceptar un salto de línea final.
validar_periodo = RegexValidator(
    r"^\d{4}-(0[1-9]|1[0-2])\Z", "El período debe tener formato YYYY-MM (por ejemplo 2026-03)."
)


class Indicador(models.Model):
    practica = models.ForeignKey("catalog.Practica", on_delete=models.PROTECT, related_name="indicadores")
    nombre = models.CharField(max_length=200)
    formula = models.TextField()
    unidad = models.CharField(max_length=40)
    periodicidad = models.CharField(max_length=20, choices=Periodicidad.choices)
    tipo = models.CharField(max_length=20, choices=TipoIndicador.choices)
    fuente = models.CharField(max_length=200, blank=True)
    responsable_datos = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="indicadores_a_cargo",
    )
    linea_base = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    meta = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    tolerancia = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    referencia_estandar = models.CharField(max_length=120, blank=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "indicadores"

    def __str__(self):
        return self.nombre

    @property
    def facultad_scope_id(self) -> int:
        return self.practica.facultad_id


class Medicion(models.Model):
    indicador = models.ForeignKey(Indicador, on_delete=models.PROTECT, related_name="mediciones")
    periodo = models.CharField(max_length=7, validators=[validar_periodo])
    valor = models.DecimalField(max_digits=16, decimal_places=4)
    estado = models.CharField(
        max_length=20, choices=EstadoMedicion.choices, default=EstadoMedicion.BORRADOR
    )
    cargado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mediciones_cargadas"
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mediciones_validadas",
    )
    validado_en = models.DateTimeField(null=True, blank=True)
    comentario_validacion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "medición"
        verbose_name_plural = "mediciones"

    def __str__(self):
        return f"{self.indicador} · {self.periodo}"

    @property
    def facultad_scope_id(self) -> int:
        return self.indicador.practica.facultad_id

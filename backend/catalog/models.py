from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords


class Dimension(models.TextChoices):
    AMBIENTAL = "ambiental", "Ambiental"
    SOCIAL = "social", "Social"
    ECONOMICA = "economica", "Económica"
    INSTITUCIONAL = "institucional", "Institucional"


class Estado(models.TextChoices):
    IDENTIFICADA = "identificada", "Identificada"
    FORMALIZADA = "formalizada", "Formalizada"
    MEDIDA = "medida", "Medida"
    OPTIMIZADA = "optimizada", "Optimizada"


ESTADOS_ORDEN = [Estado.IDENTIFICADA, Estado.FORMALIZADA, Estado.MEDIDA, Estado.OPTIMIZADA]


class Origen(models.TextChoices):
    CARGADA = "cargada", "Cargada"
    ILUSTRATIVA = "ilustrativa", "Ilustrativa"


class Region(models.Model):
    nombre = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.nombre


class Facultad(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="facultades")
    es_nivel_central = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "facultades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ODS(models.Model):
    numero = models.PositiveSmallIntegerField(
        primary_key=True, validators=[MinValueValidator(1), MaxValueValidator(17)]
    )
    nombre = models.CharField(max_length=120)

    class Meta:
        verbose_name = "ODS"
        verbose_name_plural = "ODS"
        ordering = ["numero"]

    def __str__(self):
        return f"ODS {self.numero}: {self.nombre}"


class Practica(models.Model):
    facultad = models.ForeignKey(Facultad, on_delete=models.PROTECT, related_name="practicas")
    nombre = models.CharField(max_length=200)
    dimension = models.CharField(max_length=20, choices=Dimension.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.IDENTIFICADA)
    proposito = models.TextField(blank=True)
    ods = models.ManyToManyField(ODS, blank=True, related_name="practicas")
    alcance = models.TextField(blank=True)
    actividades = models.TextField(blank=True)
    frecuencia = models.CharField(max_length=60, blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="practicas_a_cargo",
    )
    origen = models.CharField(max_length=20, choices=Origen.choices, default=Origen.CARGADA)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "práctica"
        verbose_name_plural = "prácticas"

    def __str__(self):
        return self.nombre

    def estado_siguiente(self):
        i = ESTADOS_ORDEN.index(self.estado)
        return ESTADOS_ORDEN[i + 1] if i + 1 < len(ESTADOS_ORDEN) else None

    def estado_anterior(self):
        i = ESTADOS_ORDEN.index(self.estado)
        return ESTADOS_ORDEN[i - 1] if i > 0 else None

    @property
    def facultad_scope_id(self) -> int:
        return self.facultad_id

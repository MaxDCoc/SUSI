from decimal import Decimal

from django.utils import timezone

from evidence.models import Evidencia, TipoEvidencia
from indicators.models import EstadoMedicion, Medicion


def nueva_medicion_validada(indicador, cargado_por, validador, periodo, con_evidencia=True, valor="10"):
    """Crea directamente una medición ya validada (y, opcionalmente, con una evidencia)."""
    medicion = Medicion.objects.create(
        indicador=indicador,
        periodo=periodo,
        valor=Decimal(valor),
        cargado_por=cargado_por,
        estado=EstadoMedicion.VALIDADA,
        validado_por=validador,
        validado_en=timezone.now(),
    )
    if con_evidencia:
        Evidencia.objects.create(
            medicion=medicion,
            tipo=TipoEvidencia.ENLACE,
            url="https://example.org/evidencia",
            creado_por=cargado_por,
        )
    return medicion

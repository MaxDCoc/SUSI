from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import Rol
from accounts.scope import es_admin, exigir_rol
from catalog.models import Estado, Practica
from indicators.models import EstadoMedicion, Indicador, Medicion

# Largo máximo de history_change_reason en django-simple-history.
MOTIVO_MAX = 100


def requisito_faltante(practica: Practica, destino: str) -> str | None:
    """Devuelve el mensaje del requisito que falta para pasar a `destino`, o None si se cumple."""
    if destino == Estado.FORMALIZADA:
        if practica.responsable_id is None:
            return "Falta asignar un responsable para pasar a formalizada."
    elif destino == Estado.MEDIDA:
        existe = Medicion.objects.filter(
            indicador__practica=practica,
            estado=EstadoMedicion.VALIDADA,
            evidencias__isnull=False,
        ).exists()
        if not existe:
            return (
                "Falta un indicador con al menos una medición validada y con evidencia "
                "para pasar a medida."
            )
    elif destino == Estado.OPTIMIZADA:
        existe = (
            Indicador.objects.filter(practica=practica, meta__isnull=False)
            .annotate(validadas=Count("mediciones", filter=Q(mediciones__estado=EstadoMedicion.VALIDADA)))
            .filter(validadas__gte=2)
            .exists()
        )
        if not existe:
            return (
                "Falta un indicador con meta definida y al menos dos mediciones validadas "
                "para pasar a optimizada."
            )
    return None


@transaction.atomic
def promover_practica(practica_id: int, user, desde: str | None = None) -> Practica:
    """Promueve un nivel. `desde` es el estado que el cliente cree vigente: si ya cambió (doble clic), falla."""
    practica = Practica.objects.select_for_update().get(pk=practica_id)
    exigir_rol(user, practica.facultad_scope_id, Rol.RESPONSABLE)
    if desde and desde != practica.estado:
        raise ValidationError("La práctica cambió de estado mientras tanto. Recargá la página para ver el estado actual.")
    destino = practica.estado_siguiente()
    if destino is None:
        raise ValidationError("La práctica ya está en el estado máximo (optimizada).")
    faltante = requisito_faltante(practica, destino)
    if faltante:
        raise ValidationError(faltante)
    practica.estado = destino
    practica._history_user = user
    practica.save()
    return practica


@transaction.atomic
def retroceder_practica(practica_id: int, user, motivo: str) -> Practica:
    if not es_admin(user):
        raise PermissionDenied("Solo el Administrador puede retroceder el estado de una práctica.")
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError("Se requiere un motivo para retroceder la práctica.")
    practica = Practica.objects.select_for_update().get(pk=practica_id)
    anterior = practica.estado_anterior()
    if anterior is None:
        raise ValidationError("La práctica ya está en el estado mínimo (identificada).")
    practica.estado = anterior
    practica._history_user = user
    practica._change_reason = motivo[:MOTIVO_MAX]
    practica.save()
    return practica


def _medicion_bloqueada(medicion_id: int) -> Medicion:
    return Medicion.objects.select_for_update().get(pk=medicion_id)


def _guardar(medicion: Medicion, user) -> Medicion:
    medicion._history_user = user
    medicion.save()
    return medicion


@transaction.atomic
def enviar_medicion(medicion_id: int, user) -> Medicion:
    medicion = _medicion_bloqueada(medicion_id)
    exigir_rol(user, medicion.facultad_scope_id, Rol.RESPONSABLE)
    if medicion.estado != EstadoMedicion.BORRADOR:
        raise ValidationError("Solo se puede enviar una medición en borrador.")
    medicion.estado = EstadoMedicion.ENVIADA
    return _guardar(medicion, user)


def _resolver_envio(medicion: Medicion, user, estado: str, comentario: str) -> Medicion:
    medicion.estado = estado
    medicion.validado_por = user
    medicion.validado_en = timezone.now()
    medicion.comentario_validacion = comentario
    return _guardar(medicion, user)


@transaction.atomic
def validar_medicion(medicion_id: int, user, comentario: str = "") -> Medicion:
    medicion = _medicion_bloqueada(medicion_id)
    exigir_rol(user, medicion.facultad_scope_id, Rol.VALIDADOR)
    if medicion.estado != EstadoMedicion.ENVIADA:
        raise ValidationError("Solo se puede validar una medición enviada.")
    if medicion.cargado_por_id == user.id:
        raise PermissionDenied("Quien cargó la medición no puede validarla.")
    return _resolver_envio(medicion, user, EstadoMedicion.VALIDADA, (comentario or "").strip())


@transaction.atomic
def rechazar_medicion(medicion_id: int, user, comentario: str) -> Medicion:
    medicion = _medicion_bloqueada(medicion_id)
    exigir_rol(user, medicion.facultad_scope_id, Rol.VALIDADOR)
    comentario = (comentario or "").strip()
    if not comentario:
        raise ValidationError("Se requiere un comentario para rechazar la medición.")
    if medicion.estado != EstadoMedicion.ENVIADA:
        raise ValidationError("Solo se puede rechazar una medición enviada.")
    if medicion.cargado_por_id == user.id:
        raise PermissionDenied("Quien cargó la medición no puede rechazarla.")
    return _resolver_envio(medicion, user, EstadoMedicion.RECHAZADA, comentario)


@transaction.atomic
def reabrir_medicion(medicion_id: int, user) -> Medicion:
    medicion = _medicion_bloqueada(medicion_id)
    exigir_rol(user, medicion.facultad_scope_id, Rol.RESPONSABLE)
    if medicion.estado != EstadoMedicion.RECHAZADA:
        raise ValidationError("Solo se puede reabrir una medición rechazada.")
    medicion.estado = EstadoMedicion.BORRADOR
    medicion.validado_por = None
    medicion.validado_en = None
    return _guardar(medicion, user)

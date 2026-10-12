from decimal import Decimal

import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import Membership, Rol
from catalog.models import Estado
from indicators.models import EstadoMedicion
from tests.helpers import nueva_medicion_validada
from workflow import services

pytestmark = pytest.mark.django_db


def dejar_formalizada(escenario):
    practica = escenario.practica
    practica.responsable = escenario.responsable
    practica.estado = Estado.FORMALIZADA
    practica.save()
    return practica


def dejar_medida(escenario):
    dejar_formalizada(escenario)
    nueva_medicion_validada(escenario.indicador, escenario.responsable, escenario.validador, "2026-02")
    return services.promover_practica(escenario.practica.id, escenario.responsable)


# ---------- promover_practica ----------


def test_no_se_formaliza_sin_responsable(escenario):
    with pytest.raises(ValidationError, match="responsable"):
        services.promover_practica(escenario.practica.id, escenario.responsable)


def test_formaliza_con_responsable_y_registra_quien_lo_hizo(escenario):
    escenario.practica.responsable = escenario.responsable
    escenario.practica.save()

    practica = services.promover_practica(escenario.practica.id, escenario.responsable)

    assert practica.estado == Estado.FORMALIZADA
    assert practica.history.first().history_user == escenario.responsable


def test_no_pasa_a_medida_sin_medicion_validada(escenario):
    dejar_formalizada(escenario)  # solo existe la medición en borrador

    with pytest.raises(ValidationError, match="medición validada"):
        services.promover_practica(escenario.practica.id, escenario.responsable)


def test_no_pasa_a_medida_si_la_medicion_validada_no_tiene_evidencia(escenario):
    dejar_formalizada(escenario)
    nueva_medicion_validada(
        escenario.indicador, escenario.responsable, escenario.validador, "2026-02", con_evidencia=False
    )

    with pytest.raises(ValidationError, match="evidencia"):
        services.promover_practica(escenario.practica.id, escenario.responsable)


def test_pasa_a_medida_con_medicion_validada_y_evidencia(escenario):
    practica = dejar_medida(escenario)

    assert practica.estado == Estado.MEDIDA


def test_no_pasa_a_optimizada_sin_meta(escenario):
    dejar_medida(escenario)
    nueva_medicion_validada(escenario.indicador, escenario.responsable, escenario.validador, "2026-03")

    with pytest.raises(ValidationError, match="meta"):
        services.promover_practica(escenario.practica.id, escenario.responsable)


def test_no_pasa_a_optimizada_con_una_sola_medicion_validada(escenario):
    dejar_medida(escenario)  # deja una medición validada
    escenario.indicador.meta = Decimal("100")
    escenario.indicador.save()

    with pytest.raises(ValidationError, match="dos mediciones"):
        services.promover_practica(escenario.practica.id, escenario.responsable)


def test_pasa_a_optimizada_con_meta_y_dos_mediciones_validadas(escenario):
    dejar_medida(escenario)
    nueva_medicion_validada(escenario.indicador, escenario.responsable, escenario.validador, "2026-03")
    escenario.indicador.meta = Decimal("100")
    escenario.indicador.save()

    practica = services.promover_practica(escenario.practica.id, escenario.responsable)

    assert practica.estado == Estado.OPTIMIZADA


def test_no_hay_estado_posterior_a_optimizada(escenario):
    escenario.practica.estado = Estado.OPTIMIZADA
    escenario.practica.save()

    with pytest.raises(ValidationError, match="estado máximo"):
        services.promover_practica(escenario.practica.id, escenario.responsable)


def test_promover_exige_ser_responsable_de_la_facultad(escenario, user_factory):
    with pytest.raises(PermissionDenied):
        services.promover_practica(escenario.practica.id, user_factory())


def test_un_validador_no_puede_promover(escenario):
    with pytest.raises(PermissionDenied):
        services.promover_practica(escenario.practica.id, escenario.validador)


def test_el_administrador_puede_promover(escenario, user_factory):
    escenario.practica.responsable = escenario.responsable
    escenario.practica.save()
    admin = user_factory(is_superuser=True)

    practica = services.promover_practica(escenario.practica.id, admin)

    assert practica.estado == Estado.FORMALIZADA


# ---------- retroceder_practica ----------


def test_solo_el_administrador_retrocede(escenario):
    dejar_formalizada(escenario)

    with pytest.raises(PermissionDenied):
        services.retroceder_practica(escenario.practica.id, escenario.responsable, "Error de carga")


def test_retroceder_exige_motivo(escenario, user_factory):
    dejar_formalizada(escenario)

    with pytest.raises(ValidationError, match="motivo"):
        services.retroceder_practica(escenario.practica.id, user_factory(is_superuser=True), "   ")


def test_retroceder_baja_un_estado_y_deja_el_motivo_en_el_historial(escenario, user_factory):
    dejar_formalizada(escenario)
    admin = user_factory(is_superuser=True)

    practica = services.retroceder_practica(escenario.practica.id, admin, "Dato cargado por error")

    assert practica.estado == Estado.IDENTIFICADA
    ultimo = practica.history.first()
    assert ultimo.history_change_reason == "Dato cargado por error"
    assert ultimo.history_user == admin


def test_no_se_retrocede_desde_identificada(escenario, user_factory):
    with pytest.raises(ValidationError, match="identificada"):
        services.retroceder_practica(escenario.practica.id, user_factory(is_superuser=True), "x")


# ---------- mediciones ----------


def test_enviar_pasa_de_borrador_a_enviada(escenario):
    medicion = services.enviar_medicion(escenario.medicion.id, escenario.responsable)

    assert medicion.estado == EstadoMedicion.ENVIADA


def test_solo_se_envia_desde_borrador(escenario):
    services.enviar_medicion(escenario.medicion.id, escenario.responsable)

    with pytest.raises(ValidationError, match="borrador"):
        services.enviar_medicion(escenario.medicion.id, escenario.responsable)


def test_enviar_exige_ser_responsable(escenario):
    with pytest.raises(PermissionDenied):
        services.enviar_medicion(escenario.medicion.id, escenario.validador)


def test_validar_registra_validador_fecha_y_comentario(escenario):
    services.enviar_medicion(escenario.medicion.id, escenario.responsable)

    medicion = services.validar_medicion(escenario.medicion.id, escenario.validador, "Conforme")

    assert medicion.estado == EstadoMedicion.VALIDADA
    assert medicion.validado_por == escenario.validador
    assert medicion.validado_en is not None
    assert medicion.comentario_validacion == "Conforme"


def test_no_se_valida_una_medicion_en_borrador(escenario):
    with pytest.raises(ValidationError, match="enviada"):
        services.validar_medicion(escenario.medicion.id, escenario.validador)


def test_un_responsable_sin_rol_de_validador_no_valida(escenario, user_factory):
    otro_responsable = user_factory()
    Membership.objects.create(user=otro_responsable, facultad=escenario.facultad, rol=Rol.RESPONSABLE)
    services.enviar_medicion(escenario.medicion.id, escenario.responsable)

    with pytest.raises(PermissionDenied):
        services.validar_medicion(escenario.medicion.id, otro_responsable)


# Review Focus 3: roles cruzados y doble clic
def test_no_se_valida_lo_propio_aunque_se_tengan_ambos_roles(escenario):
    Membership.objects.create(user=escenario.responsable, facultad=escenario.facultad, rol=Rol.VALIDADOR)
    services.enviar_medicion(escenario.medicion.id, escenario.responsable)

    with pytest.raises(PermissionDenied, match="no puede validarla"):
        services.validar_medicion(escenario.medicion.id, escenario.responsable)


def test_el_administrador_tampoco_valida_lo_que_cargo(escenario, user_factory):
    admin = user_factory(is_superuser=True)
    escenario.medicion.cargado_por = admin
    escenario.medicion.estado = EstadoMedicion.ENVIADA
    escenario.medicion.save()

    with pytest.raises(PermissionDenied, match="no puede validarla"):
        services.validar_medicion(escenario.medicion.id, admin)


def test_validar_dos_veces_no_pisa_al_primer_validador(escenario, user_factory):
    segundo = user_factory()
    Membership.objects.create(user=segundo, facultad=escenario.facultad, rol=Rol.VALIDADOR)
    services.enviar_medicion(escenario.medicion.id, escenario.responsable)
    services.validar_medicion(escenario.medicion.id, escenario.validador)

    with pytest.raises(ValidationError, match="enviada"):
        services.validar_medicion(escenario.medicion.id, segundo)

    escenario.medicion.refresh_from_db()
    assert escenario.medicion.validado_por == escenario.validador


def test_rechazar_exige_comentario(escenario):
    services.enviar_medicion(escenario.medicion.id, escenario.responsable)

    with pytest.raises(ValidationError, match="comentario"):
        services.rechazar_medicion(escenario.medicion.id, escenario.validador, "  ")


def test_rechazar_y_reabrir_vuelve_a_borrador(escenario):
    services.enviar_medicion(escenario.medicion.id, escenario.responsable)

    rechazada = services.rechazar_medicion(escenario.medicion.id, escenario.validador, "Falta la fuente")
    assert rechazada.estado == EstadoMedicion.RECHAZADA
    assert rechazada.comentario_validacion == "Falta la fuente"

    reabierta = services.reabrir_medicion(escenario.medicion.id, escenario.responsable)
    assert reabierta.estado == EstadoMedicion.BORRADOR
    assert reabierta.validado_por is None
    assert reabierta.validado_en is None


def test_solo_se_reabre_una_medicion_rechazada(escenario):
    with pytest.raises(ValidationError, match="rechazada"):
        services.reabrir_medicion(escenario.medicion.id, escenario.responsable)

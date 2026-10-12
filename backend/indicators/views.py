from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import Rol
from accounts.scope import exigir_rol
from evidence.models import Evidencia
from susi.queryparams import entero
from workflow import services

from .models import EstadoMedicion, Indicador, Medicion
from .serializers import IndicadorSerializer, MedicionSerializer


class IndicadorViewSet(viewsets.ModelViewSet):
    serializer_class = IndicadorSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = Indicador.objects.select_related("practica").order_by("id")
        practica = entero(self.request.query_params, "practica")
        if practica is not None:
            qs = qs.filter(practica_id=practica)
        return qs

    def perform_create(self, serializer):
        exigir_rol(self.request.user, serializer.validated_data["practica"].facultad_scope_id, Rol.RESPONSABLE)
        serializer.save()

    def perform_update(self, serializer):
        instancia = serializer.instance
        exigir_rol(self.request.user, instancia.facultad_scope_id, Rol.RESPONSABLE)
        nueva = serializer.validated_data.get("practica")
        if nueva is not None and nueva.pk != instancia.practica_id:
            raise ValidationError("No se puede cambiar la práctica de un indicador.")
        serializer.save()


def _comentario(request) -> str:
    return request.data.get("comentario", "") if hasattr(request.data, "get") else ""


class MedicionViewSet(viewsets.ModelViewSet):
    serializer_class = MedicionSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = (
            Medicion.objects.select_related("indicador__practica__facultad", "cargado_por", "validado_por")
            .prefetch_related(
                Prefetch("evidencias", queryset=Evidencia.objects.select_related("creado_por").order_by("id"))
            )
            .order_by("-id")
        )
        params = self.request.query_params
        for parametro, campo in (
            ("indicador", "indicador_id"),
            ("practica", "indicador__practica_id"),
            ("facultad", "indicador__practica__facultad_id"),
        ):
            valor = entero(params, parametro)
            if valor is not None:
                qs = qs.filter(**{campo: valor})
        if params.get("estado"):
            qs = qs.filter(estado=params["estado"])
        return qs

    def perform_create(self, serializer):
        indicador = serializer.validated_data["indicador"]
        exigir_rol(self.request.user, indicador.facultad_scope_id, Rol.RESPONSABLE)
        serializer.save(cargado_por=self.request.user)

    def perform_update(self, serializer):
        instancia = serializer.instance
        exigir_rol(self.request.user, instancia.facultad_scope_id, Rol.RESPONSABLE)
        if instancia.estado != EstadoMedicion.BORRADOR:
            raise ValidationError("Solo se pueden editar mediciones en borrador.")
        nuevo = serializer.validated_data.get("indicador")
        if nuevo is not None and nuevo.pk != instancia.indicador_id:
            raise ValidationError("No se puede cambiar el indicador de una medición.")
        # Quien modifica el borrador pasa a ser quien lo cargó: así no puede validarlo después.
        serializer.save(cargado_por=self.request.user)

    def _responder(self, pk) -> Response:
        # Se relee con el queryset de la vista para que incluya evidencias y nombres.
        return Response(self.get_serializer(self.get_queryset().get(pk=pk)).data)

    @action(detail=True, methods=["post"])
    def enviar(self, request, pk=None):
        self.get_object()
        services.enviar_medicion(pk, request.user)
        return self._responder(pk)

    @action(detail=True, methods=["post"])
    def validar(self, request, pk=None):
        self.get_object()
        services.validar_medicion(pk, request.user, _comentario(request))
        return self._responder(pk)

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        self.get_object()
        services.rechazar_medicion(pk, request.user, _comentario(request))
        return self._responder(pk)

    @action(detail=True, methods=["post"])
    def reabrir(self, request, pk=None):
        self.get_object()
        services.reabrir_medicion(pk, request.user)
        return self._responder(pk)

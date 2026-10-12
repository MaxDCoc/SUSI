from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Rol
from accounts.scope import exigir_rol
from indicators.models import Periodicidad, TipoIndicador
from susi.queryparams import entero
from workflow import services

from .models import ODS, Dimension, Estado, Facultad, Practica, Region
from .serializers import PracticaSerializer


def _opciones(choices):
    return [{"valor": valor, "etiqueta": etiqueta} for valor, etiqueta in choices]


class CatalogosView(APIView):
    def get(self, request):
        return Response(
            {
                "regiones": list(Region.objects.order_by("nombre").values("id", "nombre")),
                "facultades": list(
                    Facultad.objects.order_by("nombre").values("id", "nombre", "region_id", "es_nivel_central")
                ),
                "ods": list(ODS.objects.order_by("numero").values("numero", "nombre")),
                "dimensiones": _opciones(Dimension.choices),
                "estados": _opciones(Estado.choices),
                "periodicidades": _opciones(Periodicidad.choices),
                "tipos_indicador": _opciones(TipoIndicador.choices),
            }
        )


class PracticaViewSet(viewsets.ModelViewSet):
    serializer_class = PracticaSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = Practica.objects.select_related("facultad", "responsable").prefetch_related("ods").order_by("-id")
        params = self.request.query_params
        facultad = entero(params, "facultad")
        if facultad is not None:
            qs = qs.filter(facultad_id=facultad)
        if params.get("dimension"):
            qs = qs.filter(dimension=params["dimension"])
        if params.get("estado"):
            qs = qs.filter(estado=params["estado"])
        return qs

    def perform_create(self, serializer):
        exigir_rol(self.request.user, serializer.validated_data["facultad"].id, Rol.RESPONSABLE)
        serializer.save()

    def perform_update(self, serializer):
        usuario = self.request.user
        exigir_rol(usuario, serializer.instance.facultad_id, Rol.RESPONSABLE)
        nueva = serializer.validated_data.get("facultad")
        if nueva is not None:
            exigir_rol(usuario, nueva.id, Rol.RESPONSABLE)
        serializer.save()

    @action(detail=True, methods=["post"])
    def promover(self, request, pk=None):
        practica = self.get_object()
        actualizada = services.promover_practica(practica.pk, request.user)
        return Response(self.get_serializer(actualizada).data)

    @action(detail=True, methods=["post"])
    def retroceder(self, request, pk=None):
        practica = self.get_object()
        motivo = request.data.get("motivo", "") if hasattr(request.data, "get") else ""
        actualizada = services.retroceder_practica(practica.pk, request.user, motivo)
        return Response(self.get_serializer(actualizada).data)

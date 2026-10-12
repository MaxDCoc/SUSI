import os

from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError

from accounts.models import Rol
from accounts.scope import exigir_rol
from susi.queryparams import entero

from .models import Evidencia
from .serializers import EvidenciaSerializer


class EvidenciaViewSet(viewsets.ModelViewSet):
    serializer_class = EvidenciaSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = Evidencia.objects.select_related("medicion__indicador__practica", "practica", "creado_por").order_by("-id")
        params = self.request.query_params
        medicion = entero(params, "medicion")
        if medicion is not None:
            qs = qs.filter(medicion_id=medicion)
        practica = entero(params, "practica")
        if practica is not None:
            qs = qs.filter(practica_id=practica)
        return qs

    def perform_create(self, serializer):
        medicion = serializer.validated_data.get("medicion")
        practica = serializer.validated_data.get("practica")
        if medicion is not None:
            facultad_id = medicion.facultad_scope_id
        elif practica is not None:
            facultad_id = practica.facultad_scope_id
        else:
            raise ValidationError("La evidencia debe pertenecer a una medición o a una práctica.")
        exigir_rol(self.request.user, facultad_id, Rol.RESPONSABLE)
        serializer.save(creado_por=self.request.user)

    @action(detail=True, methods=["get"])
    def descargar(self, request, pk=None):
        evidencia = self.get_object()
        if not evidencia.archivo:
            raise NotFound("Esta evidencia es un enlace y no tiene archivo.")
        return FileResponse(
            evidencia.archivo.open("rb"),
            as_attachment=True,
            filename=os.path.basename(evidencia.archivo.name),
        )

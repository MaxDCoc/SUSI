from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .cache import con_cache
from .serializers import leer_filtros


class EmbudoView(APIView):
    def get(self, request):
        filtros = leer_filtros(request)

        def calcular():
            estados = services.embudo(services.practicas_filtradas(filtros))
            return {"total": sum(estados.values()), "estados": estados}

        return Response(con_cache("embudo", filtros, calcular))


class ResumenView(APIView):
    def get(self, request):
        filtros = leer_filtros(request)
        return Response(con_cache("resumen", filtros, lambda: services.resumen(filtros)))

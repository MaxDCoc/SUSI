import logging

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import Http404, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


def health(request):
    # No toca la base: el monitor que mantiene despierta la app le pega seguido.
    return JsonResponse({"status": "ok"})


def health_db(request):
    """Hace una consulta mínima: sirve de keep-alive de la base (Supabase pausa los proyectos gratis inactivos)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        logger.exception("La base de datos no respondió en /health/db/")
        return JsonResponse({"status": "error", "base": "no disponible"}, status=503)
    return JsonResponse({"status": "ok", "base": "ok"})


def spa(request, ruta=""):
    """Entrega el index.html del SPA para las rutas del cliente (React Router)."""
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise Http404("Falta el build del frontend: corré `npm run build` en frontend/.")
    return HttpResponse(index.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")

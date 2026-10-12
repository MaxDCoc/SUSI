from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


def spa(request, ruta=""):
    """Entrega el index.html del SPA para las rutas del cliente (React Router)."""
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise Http404("Falta el build del frontend: corré `npm run build` en frontend/.")
    return HttpResponse(index.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")

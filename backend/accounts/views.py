import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .scope import es_admin


def _datos_sesion(user) -> dict:
    if not user.is_authenticated:
        return {"authenticated": False, "membresias": []}
    membresias = [
        {"facultad": m.facultad_id, "facultad_nombre": m.facultad.nombre, "rol": m.rol}
        for m in user.membresias.select_related("facultad").order_by("facultad__nombre", "rol")
    ]
    return {
        "authenticated": True,
        "id": user.id,
        "username": user.get_username(),
        "es_admin": es_admin(user),
        "membresias": membresias,
    }


@require_GET
@ensure_csrf_cookie
def sesion(request):
    return JsonResponse(_datos_sesion(request.user))


@require_POST
def login_view(request):
    try:
        datos = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "El cuerpo debe ser JSON válido."}, status=400)
    if not isinstance(datos, dict):
        return JsonResponse({"detail": "El cuerpo debe ser un objeto JSON."}, status=400)
    usuario = authenticate(
        request, username=str(datos.get("username", "")), password=str(datos.get("password", ""))
    )
    if usuario is None:
        return JsonResponse({"detail": "Usuario o contraseña incorrectos."}, status=400)
    login(request, usuario)
    return JsonResponse(_datos_sesion(request.user))


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse(_datos_sesion(request.user))

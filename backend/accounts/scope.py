from rest_framework.exceptions import PermissionDenied

from .models import Membership


def es_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.is_superuser)


def tiene_rol(user, facultad_id: int, rol: str) -> bool:
    if es_admin(user):
        return True
    if not (user and user.is_authenticated):
        return False
    return Membership.objects.filter(user=user, facultad_id=facultad_id, rol=rol).exists()


def exigir_rol(user, facultad_id: int, rol: str) -> None:
    if not tiene_rol(user, facultad_id, rol):
        raise PermissionDenied(f"Se requiere el rol {rol} en esta facultad.")

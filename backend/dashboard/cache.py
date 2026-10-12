import hashlib
import json

from django.core.cache import cache

_CLAVE_VERSION = "dashboard:version"
TTL_SEGUNDOS = 60


def _version() -> int:
    version = cache.get(_CLAVE_VERSION)
    if version is None:
        cache.add(_CLAVE_VERSION, 1, None)
        version = cache.get(_CLAVE_VERSION) or 1
    return version


def invalidar(*args, **kwargs) -> None:
    """Sube la versión del caché; sirve como receptor de señales."""
    try:
        cache.incr(_CLAVE_VERSION)
    except ValueError:
        cache.set(_CLAVE_VERSION, 2, None)


def con_cache(prefijo: str, filtros: dict, calcular):
    huella = hashlib.sha256(json.dumps(filtros, sort_keys=True).encode()).hexdigest()
    clave = f"dashboard:{prefijo}:{_version()}:{huella}"
    datos = cache.get(clave)
    if datos is None:
        datos = calcular()
        cache.set(clave, datos, TTL_SEGUNDOS)
    return datos

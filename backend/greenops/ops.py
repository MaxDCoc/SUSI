OPS_NUCLEO = ("practica.crear", "practica.consultar", "medicion.validar")
UNIDAD_FUNCIONAL_OPS = 1000


def nombre_operacion(method: str, url_name: str | None) -> str | None:
    """Traduce (método HTTP, nombre de URL) a un nombre lógico como `practica.crear`."""
    if not url_name:
        return None
    if url_name.endswith("-list"):
        base = url_name[: -len("-list")]
        return f"{base}.consultar" if method in ("GET", "HEAD") else f"{base}.crear"
    if url_name.endswith("-detail"):
        base = url_name[: -len("-detail")]
        return f"{base}.consultar" if method in ("GET", "HEAD") else f"{base}.actualizar"
    return url_name.replace("-", ".")

from rest_framework.exceptions import ValidationError


def entero(params, nombre: str) -> int | None:
    valor = params.get(nombre)
    if valor in (None, ""):
        return None
    try:
        return int(valor)
    except ValueError:
        raise ValidationError({nombre: "Debe ser un número entero."}) from None

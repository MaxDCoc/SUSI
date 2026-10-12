import os

from django.core.exceptions import ValidationError

TAMANO_MAXIMO = 2 * 1024 * 1024

# Extensión permitida -> firmas ("magic bytes") aceptadas.
FIRMAS = {
    ".pdf": (b"%PDF",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
}


def validar_archivo(archivo) -> None:
    extension = os.path.splitext(archivo.name)[1].lower()
    if extension not in FIRMAS:
        raise ValidationError("Solo se aceptan archivos PDF, PNG o JPG.")
    if archivo.size == 0:
        raise ValidationError("El archivo está vacío.")
    if archivo.size > TAMANO_MAXIMO:
        raise ValidationError("El archivo supera el máximo de 2 MB.")
    cabecera = archivo.read(8)
    archivo.seek(0)
    if not any(cabecera.startswith(firma) for firma in FIRMAS[extension]):
        raise ValidationError("El contenido del archivo no coincide con su extensión.")

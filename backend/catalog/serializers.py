from rest_framework import serializers

from .models import Practica


class PracticaSerializer(serializers.ModelSerializer):
    facultad_nombre = serializers.CharField(source="facultad.nombre", read_only=True)
    responsable_nombre = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = Practica
        fields = [
            "id",
            "facultad",
            "facultad_nombre",
            "nombre",
            "dimension",
            "estado",
            "proposito",
            "ods",
            "alcance",
            "actividades",
            "frecuencia",
            "responsable",
            "responsable_nombre",
            "origen",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["estado", "origen", "creado_en", "actualizado_en"]

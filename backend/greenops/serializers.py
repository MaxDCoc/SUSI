from rest_framework import serializers

from .models import ParametroSCI


class ParametroSCISerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametroSCI
        fields = [
            "id",
            "version",
            "potencia_cpu_w",
            "intensidad_carbono_g_kwh",
            "fuente_intensidad",
            "fecha_intensidad",
            "te_g",
            "el_horas",
            "rs",
            "tr",
            "supuestos",
            "creado_en",
        ]
        read_only_fields = ["version", "creado_en"]

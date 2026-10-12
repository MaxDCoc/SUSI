from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from rest_framework import serializers

from .models import Evidencia


class EvidenciaResumenSerializer(serializers.ModelSerializer):
    """Lectura: se anida dentro de la medición."""

    archivo_descarga = serializers.SerializerMethodField()
    creado_por_nombre = serializers.CharField(source="creado_por.username", read_only=True)

    class Meta:
        model = Evidencia
        fields = ["id", "tipo", "url", "descripcion", "archivo_descarga", "creado_por_nombre", "creado_en"]

    def get_archivo_descarga(self, obj):
        return reverse("evidencia-descargar", args=[obj.pk]) if obj.archivo else None


class EvidenciaSerializer(EvidenciaResumenSerializer):
    class Meta(EvidenciaResumenSerializer.Meta):
        fields = EvidenciaResumenSerializer.Meta.fields + ["medicion", "practica", "archivo"]
        extra_kwargs = {"archivo": {"write_only": True, "required": False}}

    def validate(self, attrs):
        # ModelSerializer no llama a Model.clean(); se reutilizan las reglas del modelo.
        try:
            Evidencia(**attrs).clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return attrs

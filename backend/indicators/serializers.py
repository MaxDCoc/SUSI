from rest_framework import serializers

from evidence.serializers import EvidenciaResumenSerializer

from .models import Indicador, Medicion


class IndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicador
        fields = [
            "id",
            "practica",
            "nombre",
            "formula",
            "unidad",
            "periodicidad",
            "tipo",
            "fuente",
            "responsable_datos",
            "linea_base",
            "meta",
            "tolerancia",
            "referencia_estandar",
        ]


class MedicionSerializer(serializers.ModelSerializer):
    indicador_nombre = serializers.CharField(source="indicador.nombre", read_only=True)
    unidad = serializers.CharField(source="indicador.unidad", read_only=True)
    practica_id = serializers.IntegerField(source="indicador.practica_id", read_only=True)
    practica_nombre = serializers.CharField(source="indicador.practica.nombre", read_only=True)
    practica_origen = serializers.CharField(source="indicador.practica.origen", read_only=True)
    facultad_id = serializers.IntegerField(source="indicador.practica.facultad_id", read_only=True)
    facultad_nombre = serializers.CharField(source="indicador.practica.facultad.nombre", read_only=True)
    cargado_por_nombre = serializers.CharField(source="cargado_por.username", read_only=True)
    validado_por_nombre = serializers.CharField(source="validado_por.username", read_only=True, default=None)
    evidencias = EvidenciaResumenSerializer(many=True, read_only=True)
    n_evidencias = serializers.SerializerMethodField()

    class Meta:
        model = Medicion
        fields = [
            "id",
            "indicador",
            "indicador_nombre",
            "unidad",
            "practica_id",
            "practica_nombre",
            "practica_origen",
            "facultad_id",
            "facultad_nombre",
            "periodo",
            "valor",
            "estado",
            "cargado_por",
            "cargado_por_nombre",
            "validado_por",
            "validado_por_nombre",
            "validado_en",
            "comentario_validacion",
            "creado_en",
            "evidencias",
            "n_evidencias",
        ]
        read_only_fields = [
            "estado",
            "cargado_por",
            "validado_por",
            "validado_en",
            "comentario_validacion",
            "creado_en",
        ]

    def get_n_evidencias(self, obj):
        return len(obj.evidencias.all())  # usa el prefetch de la vista

from rest_framework import serializers

from catalog.models import Dimension


class FiltrosSerializer(serializers.Serializer):
    facultad = serializers.IntegerField(required=False, min_value=1)
    region = serializers.IntegerField(required=False, min_value=1)
    dimension = serializers.ChoiceField(choices=Dimension.choices, required=False)
    ods = serializers.IntegerField(required=False, min_value=1, max_value=17)


def leer_filtros(request) -> dict:
    serializer = FiltrosSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    return dict(serializer.validated_data)

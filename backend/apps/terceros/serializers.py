from rest_framework import serializers
from .models import Tercero
from .utils import validar_nit


class TerceroSerializer(serializers.ModelSerializer):
    nit_valido = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tercero
        fields = '__all__'
        read_only_fields = ['id', 'empresa', 'created_at', 'updated_at']

    def get_nit_valido(self, obj):
        if obj.nit:
            return validar_nit(obj.nit)
        return None

    def validate_nit(self, value):
        if value and not validar_nit(value):
            raise serializers.ValidationError(
                "El NIT no es válido. Verifique el dígito verificador."
            )
        return value

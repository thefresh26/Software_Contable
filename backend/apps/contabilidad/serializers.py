from rest_framework import serializers
from .models import CuentaPUC, AsientoContable, MovimientoContable, CentroCosto


class CentroCostoSerializer(serializers.ModelSerializer):
    padre_nombre = serializers.CharField(source='padre.nombre', read_only=True)

    class Meta:
        model = CentroCosto
        fields = '__all__'
        read_only_fields = ['id']


class CuentaPUCSerializer(serializers.ModelSerializer):
    padre_nombre = serializers.CharField(source='padre.nombre', read_only=True)
    saldo = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = CuentaPUC
        fields = '__all__'
        read_only_fields = ['id']


class MovimientoContableSerializer(serializers.ModelSerializer):
    cuenta_codigo = serializers.CharField(source='cuenta.codigo', read_only=True)
    cuenta_nombre = serializers.CharField(source='cuenta.nombre', read_only=True)
    centro_costo_nombre = serializers.CharField(source='centro_costo.nombre', read_only=True)

    class Meta:
        model = MovimientoContable
        fields = '__all__'


class MovimientoContableInputSerializer(serializers.ModelSerializer):
    """Usado en la creación anidada de asientos (sin campo asiento)."""
    class Meta:
        model = MovimientoContable
        exclude = ['asiento']


class AsientoContableSerializer(serializers.ModelSerializer):
    movimientos = MovimientoContableSerializer(many=True, read_only=True)
    esta_cuadrado = serializers.BooleanField(read_only=True)

    class Meta:
        model = AsientoContable
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class AsientoContableCreateSerializer(serializers.ModelSerializer):
    movimientos = MovimientoContableInputSerializer(many=True)
    esta_cuadrado = serializers.BooleanField(read_only=True)

    class Meta:
        model = AsientoContable
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        movimientos = data.get('movimientos', [])
        total_debito = sum(m.get('debito', 0) for m in movimientos)
        total_credito = sum(m.get('credito', 0) for m in movimientos)
        if total_debito != total_credito:
            raise serializers.ValidationError(
                f'El asiento no está cuadrado: débitos={total_debito}, créditos={total_credito}'
            )
        return data

    def create(self, validated_data):
        movimientos_data = validated_data.pop('movimientos')
        asiento = AsientoContable.objects.create(**validated_data)
        for mov in movimientos_data:
            MovimientoContable.objects.create(asiento=asiento, **mov)
        return asiento

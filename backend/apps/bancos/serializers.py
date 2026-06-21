from decimal import Decimal

from rest_framework import serializers

from .models import (
    CuentaBancaria, ExtractoBancario, MovimientoBancario,
    ConciliacionBancaria, PartidaConciliacion,
)


class CuentaBancariaSerializer(serializers.ModelSerializer):
    cuenta_contable_nombre = serializers.CharField(source='cuenta_contable.nombre', read_only=True)
    cuenta_contable_codigo = serializers.CharField(source='cuenta_contable.codigo', read_only=True)

    class Meta:
        model = CuentaBancaria
        fields = '__all__'
        read_only_fields = ['id', 'empresa', 'created_at', 'saldo_actual']


class MovimientoBancarioSerializer(serializers.ModelSerializer):
    asiento_descripcion = serializers.CharField(source='asiento_contable.descripcion', read_only=True)

    class Meta:
        model = MovimientoBancario
        fields = '__all__'
        read_only_fields = ['id', 'extracto', 'conciliado', 'asiento_contable']


class ExtractoBancarioSerializer(serializers.ModelSerializer):
    cuenta_nombre = serializers.CharField(source='cuenta.nombre', read_only=True)
    movimientos_count = serializers.IntegerField(source='movimientos.count', read_only=True)

    class Meta:
        model = ExtractoBancario
        fields = '__all__'
        read_only_fields = [
            'id', 'empresa', 'created_at', 'estado',
            'periodo_inicio', 'periodo_fin', 'saldo_final_extracto',
            'total_debitos', 'total_creditos', 'archivo_original',
        ]


class ImportarExtractoSerializer(serializers.Serializer):
    archivo = serializers.FileField()
    cuenta_id = serializers.PrimaryKeyRelatedField(queryset=CuentaBancaria.objects.filter(activa=True))
    saldo_inicial = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))


class ConciliarManualSerializer(serializers.Serializer):
    asiento_id = serializers.IntegerField()

    def validate_asiento_id(self, value):
        from apps.contabilidad.models import AsientoContable
        try:
            return AsientoContable.objects.get(pk=value)
        except AsientoContable.DoesNotExist:
            raise serializers.ValidationError('No existe un asiento contable con ese id')


class PartidaConciliacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartidaConciliacion
        fields = '__all__'
        read_only_fields = ['id']


class ConciliacionBancariaSerializer(serializers.ModelSerializer):
    cuenta_nombre = serializers.CharField(source='cuenta.nombre', read_only=True)
    partidas = PartidaConciliacionSerializer(many=True, read_only=True)

    class Meta:
        model = ConciliacionBancaria
        fields = '__all__'
        read_only_fields = [
            'id', 'empresa', 'created_at', 'finalizada_at', 'estado',
            'saldo_extracto', 'saldo_libros', 'diferencia',
        ]


class CrearConciliacionSerializer(serializers.Serializer):
    extracto = serializers.PrimaryKeyRelatedField(queryset=ExtractoBancario.objects.all())
    notas = serializers.CharField(required=False, allow_blank=True, default='')

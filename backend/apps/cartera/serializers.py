from rest_framework import serializers
from .models import CuentaPorCobrar, CuentaPorPagar, PagoRecibido, PagoRealizado, DescuentoProntoPago


class DescuentoProntoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescuentoProntoPago
        fields = '__all__'
        read_only_fields = ['id', 'valor_descuento', 'aplicado', 'fecha_aplicacion', 'created_at']


class PagoRecibidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoRecibido
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class PagoRealizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoRealizado
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class CuentaPorCobrarSerializer(serializers.ModelSerializer):
    tercero_nombre = serializers.CharField(source='tercero.nombre', read_only=True)
    factura_numero = serializers.CharField(source='factura.numero', read_only=True)
    pagos = PagoRecibidoSerializer(many=True, read_only=True)

    class Meta:
        model = CuentaPorCobrar
        fields = '__all__'
        read_only_fields = ['id', 'empresa', 'created_at', 'valor_pagado', 'valor_pendiente', 'estado']


class CuentaPorPagarSerializer(serializers.ModelSerializer):
    tercero_nombre = serializers.CharField(source='tercero.nombre', read_only=True)
    factura_numero = serializers.CharField(source='factura.numero', read_only=True)
    pagos = PagoRealizadoSerializer(many=True, read_only=True)

    class Meta:
        model = CuentaPorPagar
        fields = '__all__'
        read_only_fields = ['id', 'empresa', 'created_at', 'valor_pagado', 'valor_pendiente', 'estado']


class RegistrarPagoSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    valor = serializers.DecimalField(max_digits=15, decimal_places=2)
    medio_pago = serializers.ChoiceField(choices=['efectivo', 'transferencia', 'cheque'])
    referencia = serializers.CharField(max_length=100, required=False, allow_blank=True)
    observacion = serializers.CharField(required=False, allow_blank=True)

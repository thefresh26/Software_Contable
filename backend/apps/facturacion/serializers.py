from rest_framework import serializers
from .models import Factura, DetalleFactura, TipoRetencion, RetencionFactura


class TipoRetencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoRetencion
        fields = '__all__'


class RetencionFacturaSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source='tipo_retencion.nombre', read_only=True)

    class Meta:
        model = RetencionFactura
        fields = '__all__'
        read_only_fields = ['id']


class DetalleFacturaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = DetalleFactura
        fields = '__all__'
        read_only_fields = ['id', 'subtotal', 'iva_valor', 'total']


class FacturaSerializer(serializers.ModelSerializer):
    detalles = DetalleFacturaSerializer(many=True, read_only=True)
    retenciones = RetencionFacturaSerializer(many=True, read_only=True)
    tercero_nombre = serializers.CharField(source='tercero.nombre', read_only=True)
    total_retenciones = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    neto_pagar = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Factura
        fields = '__all__'
        read_only_fields = ['id', 'numero', 'subtotal', 'iva', 'descuento', 'total', 'estado', 'created_at']


class RetencionInputSerializer(serializers.Serializer):
    tipo_retencion = serializers.PrimaryKeyRelatedField(queryset=TipoRetencion.objects.filter(activo=True))
    base = serializers.DecimalField(max_digits=15, decimal_places=2)
    porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2)
    valor = serializers.DecimalField(max_digits=15, decimal_places=2)


class DetalleFacturaInputSerializer(serializers.ModelSerializer):
    """Serializer para detalles en el contexto de creación de factura (sin campo factura)."""
    class Meta:
        model = DetalleFactura
        exclude = ['factura']
        read_only_fields = ['subtotal', 'iva_valor', 'total']


class FacturaCreateSerializer(serializers.ModelSerializer):
    detalles = DetalleFacturaInputSerializer(many=True)
    retenciones = RetencionInputSerializer(many=True, required=False)

    class Meta:
        model = Factura
        fields = ['tipo', 'tercero', 'fecha', 'fecha_vencimiento', 'observaciones', 'detalles', 'retenciones']

    def create(self, validated_data):
        from django.db import transaction
        detalles_data = validated_data.pop('detalles')
        retenciones_data = validated_data.pop('retenciones', [])
        with transaction.atomic():
            factura = Factura.objects.create(**validated_data)
            for det in detalles_data:
                DetalleFactura.objects.create(factura=factura, **det)
            factura.recalcular_totales()
            for ret in retenciones_data:
                RetencionFactura.objects.create(factura=factura, **ret)
        return factura

from rest_framework import serializers
from .models import Cotizacion, DetalleCotizacion, Presupuesto, ItemPresupuesto


class DetalleCotizacionSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = DetalleCotizacion
        fields = '__all__'
        read_only_fields = ['id', 'subtotal', 'iva_valor', 'total']


class CotizacionSerializer(serializers.ModelSerializer):
    detalles = DetalleCotizacionSerializer(many=True, read_only=True)
    tercero_nombre = serializers.CharField(source='tercero.nombre', read_only=True)

    class Meta:
        model = Cotizacion
        fields = '__all__'
        read_only_fields = ['id', 'numero', 'subtotal', 'iva', 'total', 'created_at']


class DetalleCotizacionInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleCotizacion
        exclude = ['cotizacion']
        read_only_fields = ['subtotal', 'iva_valor', 'total']


class CotizacionCreateSerializer(serializers.ModelSerializer):
    detalles = DetalleCotizacionInputSerializer(many=True)

    class Meta:
        model = Cotizacion
        fields = ['tercero', 'fecha', 'fecha_vencimiento', 'observaciones', 'terminos', 'detalles']

    def create(self, validated_data):
        from django.db import transaction
        detalles_data = validated_data.pop('detalles')
        with transaction.atomic():
            cotizacion = Cotizacion.objects.create(**validated_data)
            for det in detalles_data:
                DetalleCotizacion.objects.create(cotizacion=cotizacion, **det)
            cotizacion.recalcular_totales()
        return cotizacion


class ItemPresupuestoSerializer(serializers.ModelSerializer):
    cuenta_nombre = serializers.CharField(source='cuenta.nombre', read_only=True)
    cuenta_codigo = serializers.CharField(source='cuenta.codigo', read_only=True)

    class Meta:
        model = ItemPresupuesto
        fields = '__all__'


class ItemPresupuestoInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPresupuesto
        exclude = ['presupuesto']


class PresupuestoSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = Presupuesto
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_items(self, obj):
        return ItemPresupuestoSerializer(obj.items.all(), many=True).data


class PresupuestoCreateSerializer(serializers.ModelSerializer):
    items = ItemPresupuestoInputSerializer(many=True)

    class Meta:
        model = Presupuesto
        fields = ['nombre', 'periodo_inicio', 'periodo_fin', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        presupuesto = Presupuesto.objects.create(**validated_data)
        for item in items_data:
            ItemPresupuesto.objects.create(presupuesto=presupuesto, **item)
        return presupuesto

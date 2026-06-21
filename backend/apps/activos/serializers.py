from rest_framework import serializers
from .models import CategoriaActivo, ActivoFijo, DepreciacionMensual, BajaActivo


class CategoriaActivoSerializer(serializers.ModelSerializer):
    cuenta_activo_codigo = serializers.CharField(source='cuenta_activo.codigo', read_only=True)
    cuenta_depreciacion_codigo = serializers.CharField(source='cuenta_depreciacion.codigo', read_only=True)
    cuenta_gasto_depreciacion_codigo = serializers.CharField(source='cuenta_gasto_depreciacion.codigo', read_only=True)

    class Meta:
        model = CategoriaActivo
        fields = '__all__'
        read_only_fields = ['id', 'empresa']


class ActivoFijoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    porcentaje_depreciado = serializers.FloatField(read_only=True)

    class Meta:
        model = ActivoFijo
        fields = '__all__'
        read_only_fields = ['id', 'empresa', 'valor_depreciado_acumulado', 'valor_en_libros', 'estado', 'created_at']


class ActivoFijoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivoFijo
        exclude = ['empresa', 'valor_depreciado_acumulado', 'valor_en_libros', 'estado', 'created_at']

    def create(self, validated_data):
        validated_data.setdefault('valor_en_libros', validated_data['valor_compra'])
        return ActivoFijo.objects.create(**validated_data)


class DepreciacionMensualSerializer(serializers.ModelSerializer):
    activo_codigo = serializers.CharField(source='activo.codigo', read_only=True)
    asiento_id = serializers.IntegerField(source='asiento.id', read_only=True)

    class Meta:
        model = DepreciacionMensual
        fields = '__all__'


class BajaActivoSerializer(serializers.ModelSerializer):
    activo_codigo = serializers.CharField(source='activo.codigo', read_only=True)
    activo_nombre = serializers.CharField(source='activo.nombre', read_only=True)
    asiento_id = serializers.IntegerField(source='asiento.id', read_only=True)

    class Meta:
        model = BajaActivo
        fields = '__all__'
        read_only_fields = ['id', 'utilidad_perdida', 'asiento', 'created_at']

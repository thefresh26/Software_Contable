from rest_framework import serializers
from .models import Categoria, Producto, MovimientoInventario


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
        read_only_fields = ['empresa']


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    bajo_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = '__all__'
        read_only_fields = ['id', 'empresa', 'created_at', 'updated_at']


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = '__all__'
        read_only_fields = ['id', 'fecha', 'stock_anterior', 'stock_nuevo']


class AjusteStockSerializer(serializers.Serializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    cantidad = serializers.IntegerField()
    motivo = serializers.CharField(max_length=200)

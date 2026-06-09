from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction

from apps.empresas.mixins import EmpresaFilterMixin
from .models import Categoria, Producto, MovimientoInventario
from .serializers import (
    CategoriaSerializer, ProductoSerializer,
    MovimientoInventarioSerializer, AjusteStockSerializer,
)


class CategoriaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    search_fields = ['nombre']

    def create(self, request, *args, **kwargs):
        serializer = CategoriaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(empresa=getattr(request, 'empresa_activa', None))
        return Response(CategoriaSerializer(obj).data, status=status.HTTP_201_CREATED)


class ProductoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('categoria').all()
    serializer_class = ProductoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo', 'categoria']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering_fields = ['nombre', 'stock_actual', 'precio_venta']

    def create(self, request, *args, **kwargs):
        serializer = ProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto = serializer.save(empresa=getattr(request, 'empresa_activa', None))
        return Response(
            ProductoSerializer(self.get_queryset().get(pk=producto.pk)).data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('stock_bajo') == 'true':
            # productos cuyo stock_actual <= stock_minimo
            from django.db.models import F
            qs = qs.filter(stock_actual__lte=F('stock_minimo'))
        return qs


class MovimientoInventarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovimientoInventario.objects.select_related('producto').all()
    serializer_class = MovimientoInventarioSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['producto', 'tipo']
    ordering = ['-fecha']


class AjusteStockView(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def ajuste(self, request):
        serializer = AjusteStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        producto = data['producto']
        cantidad = data['cantidad']
        motivo = data['motivo']

        with transaction.atomic():
            stock_anterior = producto.stock_actual
            stock_nuevo = stock_anterior + cantidad
            if stock_nuevo < 0:
                return Response(
                    {'error': 'El stock no puede quedar negativo.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            producto.stock_actual = stock_nuevo
            producto.save(update_fields=['stock_actual'])
            mov = MovimientoInventario.objects.create(
                producto=producto,
                tipo='ajuste',
                cantidad=cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_nuevo,
                motivo=motivo,
            )

        return Response(MovimientoInventarioSerializer(mov).data, status=status.HTTP_201_CREATED)

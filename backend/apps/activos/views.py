import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.empresas.mixins import EmpresaFilterMixin
from .models import CategoriaActivo, ActivoFijo, DepreciacionMensual, BajaActivo
from .serializers import (
    CategoriaActivoSerializer, ActivoFijoSerializer, ActivoFijoCreateSerializer,
    DepreciacionMensualSerializer, BajaActivoSerializer,
)
from .utils import proyectar_tabla
from .servicios import aplicar_depreciacion, dar_baja_activo


def _parse_periodo(valor):
    if not valor:
        return None
    partes = valor.split('-')
    return datetime.date(int(partes[0]), int(partes[1]), 1)


class CategoriaActivoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = CategoriaActivo.objects.select_related('cuenta_activo', 'cuenta_depreciacion', 'cuenta_gasto_depreciacion').all()
    serializer_class = CategoriaActivoSerializer


class ActivoFijoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = ActivoFijo.objects.select_related('categoria', 'proveedor').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'categoria']
    search_fields = ['codigo', 'nombre', 'numero_serie']
    ordering = ['codigo']

    def get_serializer_class(self):
        return ActivoFijoCreateSerializer if self.action == 'create' else ActivoFijoSerializer

    def create(self, request, *args, **kwargs):
        serializer = ActivoFijoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activo = serializer.save(empresa=getattr(request, 'empresa_activa', None))
        return Response(ActivoFijoSerializer(activo).data, status=status.HTTP_201_CREATED)

    # ─── Tabla y depreciaciones ──────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='tabla-depreciacion')
    def tabla_depreciacion(self, request, pk=None):
        activo = self.get_object()
        return Response({
            'activo': f'{activo.nombre} - {activo.codigo}',
            'valor_compra': activo.valor_compra,
            'valor_residual': activo.valor_residual,
            'vida_util_meses': activo.vida_util_años * 12,
            'tabla': proyectar_tabla(activo),
        })

    @action(detail=True, methods=['get'])
    def depreciaciones(self, request, pk=None):
        activo = self.get_object()
        qs = activo.depreciaciones.order_by('-periodo')
        return Response(DepreciacionMensualSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='aplicar-depreciacion')
    def aplicar_depreciacion_individual(self, request, pk=None):
        activo = self.get_object()
        periodo = _parse_periodo(request.data.get('periodo'))
        if not periodo:
            return Response({'error': 'Debe indicar el período en formato YYYY-MM.'}, status=400)
        dep, creado = aplicar_depreciacion(activo, periodo)
        if dep is None:
            return Response({'error': 'No se generó depreciación para ese período (activo no elegible o ya totalmente depreciado).'}, status=400)
        return Response({
            'creado': creado,
            'depreciacion': DepreciacionMensualSerializer(dep).data,
        })

    @action(detail=False, methods=['post'], url_path='aplicar-depreciacion-mes')
    def aplicar_depreciacion_mes(self, request):
        periodo = _parse_periodo(request.data.get('periodo'))
        if not periodo:
            return Response({'error': 'Debe indicar el período en formato YYYY-MM.'}, status=400)

        resultados = []
        with transaction.atomic():
            for activo in ActivoFijo.objects.filter(estado='activo'):
                dep, creado = aplicar_depreciacion(activo, periodo)
                if dep is not None:
                    resultados.append({
                        'activo': activo.codigo,
                        'creado': creado,
                        'valor_depreciacion': dep.valor_depreciacion,
                    })
        return Response({
            'periodo': periodo.strftime('%Y-%m'),
            'aplicadas': len([r for r in resultados if r['creado']]),
            'ya_existian': len([r for r in resultados if not r['creado']]),
            'detalle': resultados,
        })

    # ─── Bajas ──────────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='dar-baja')
    def dar_baja(self, request, pk=None):
        activo = self.get_object()
        if activo.estado in ('dado_baja', 'vendido'):
            return Response({'error': 'El activo ya fue dado de baja.'}, status=400)

        fecha = request.data.get('fecha')
        motivo = request.data.get('motivo', '')
        valor_venta = Decimal(str(request.data.get('valor_venta', 0) or 0))
        observaciones = request.data.get('observaciones', '')
        if not fecha or not motivo:
            return Response({'error': 'Debe indicar fecha y motivo.'}, status=400)

        baja = dar_baja_activo(
            activo,
            fecha=datetime.date.fromisoformat(fecha),
            motivo=motivo,
            valor_venta=valor_venta,
            observaciones=observaciones,
        )
        return Response(BajaActivoSerializer(baja).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def bajas(self, request):
        qs = BajaActivo.objects.select_related('activo', 'asiento').order_by('-fecha')
        return Response(BajaActivoSerializer(qs, many=True).data)

    # ─── Reportes ───────────────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='reportes/resumen')
    def reporte_resumen(self, request):
        qs = ActivoFijo.objects.all()
        agregados = qs.aggregate(
            valor_bruto=Sum('valor_compra'),
            depreciacion_acumulada=Sum('valor_depreciado_acumulado'),
            valor_en_libros=Sum('valor_en_libros'),
        )
        return Response({
            'total_activos': qs.count(),
            'activos_activos': qs.filter(estado='activo').count(),
            'valor_bruto': agregados['valor_bruto'] or 0,
            'depreciacion_acumulada': agregados['depreciacion_acumulada'] or 0,
            'valor_en_libros': agregados['valor_en_libros'] or 0,
        })

    @action(detail=False, methods=['get'], url_path='reportes/por-categoria')
    def reporte_por_categoria(self, request):
        resultado = []
        for cat in CategoriaActivo.objects.all():
            qs = cat.activos.all()
            agregados = qs.aggregate(
                valor_bruto=Sum('valor_compra'),
                depreciacion_acumulada=Sum('valor_depreciado_acumulado'),
                valor_en_libros=Sum('valor_en_libros'),
            )
            resultado.append({
                'categoria': cat.nombre,
                'total_activos': qs.count(),
                'valor_bruto': agregados['valor_bruto'] or 0,
                'depreciacion_acumulada': agregados['depreciacion_acumulada'] or 0,
                'valor_en_libros': agregados['valor_en_libros'] or 0,
            })
        return Response(resultado)

    @action(detail=False, methods=['get'], url_path='reportes/proximos-depreciar')
    def reporte_proximos_depreciar(self, request):
        hoy = datetime.date.today()
        total_meses = hoy.year * 12 + (hoy.month - 1) + 12
        limite = datetime.date(total_meses // 12, (total_meses % 12) + 1, 1)
        resultado = []
        for activo in ActivoFijo.objects.filter(estado='activo').select_related('categoria'):
            disponible = activo.valor_en_libros - activo.valor_residual
            if disponible <= 0:
                continue
            tabla = proyectar_tabla(activo)
            for fila in tabla:
                if Decimal(str(fila['valor_en_libros'])) <= activo.valor_residual:
                    periodo_fin = datetime.datetime.strptime(fila['periodo'], '%Y-%m').date()
                    if periodo_fin <= limite:
                        resultado.append({
                            'codigo': activo.codigo,
                            'nombre': activo.nombre,
                            'categoria': activo.categoria.nombre,
                            'valor_en_libros_actual': activo.valor_en_libros,
                            'periodo_fin_depreciacion': fila['periodo'],
                        })
                    break
        return Response(resultado)

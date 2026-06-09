from decimal import Decimal

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.empresas.mixins import EmpresaFilterMixin
from .models import (
    CuentaBancaria, ExtractoBancario, MovimientoBancario,
    ConciliacionBancaria, PartidaConciliacion,
)
from .serializers import (
    CuentaBancariaSerializer, ExtractoBancarioSerializer, MovimientoBancarioSerializer,
    ConciliacionBancariaSerializer, PartidaConciliacionSerializer,
    ImportarExtractoSerializer, ConciliarManualSerializer, CrearConciliacionSerializer,
)
from .services import calcular_saldo_libros, conciliar_automatico, generar_reporte_conciliacion
from .importador import importar_extracto


class CuentaBancariaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = CuentaBancaria.objects.select_related('cuenta_contable').all()
    serializer_class = CuentaBancariaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['activa', 'tipo', 'banco']

    @action(detail=True, methods=['get'])
    def saldo(self, request, pk=None):
        cuenta = self.get_object()
        hoy = timezone.now().date()
        saldo_libros = calcular_saldo_libros(cuenta, cuenta.created_at.date(), hoy)
        ultimo_extracto = cuenta.extractos.order_by('-periodo_fin').first()
        saldo_extracto = ultimo_extracto.saldo_final_extracto if ultimo_extracto else None
        diferencia = (saldo_extracto - saldo_libros) if saldo_extracto is not None else None
        return Response({
            'saldo_libros': saldo_libros,
            'saldo_extracto': saldo_extracto,
            'diferencia': diferencia,
        })


class ExtractoBancarioViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = ExtractoBancario.objects.select_related('cuenta').all()
    serializer_class = ExtractoBancarioSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cuenta', 'estado']

    @action(detail=True, methods=['get'])
    def movimientos(self, request, pk=None):
        extracto = self.get_object()
        return Response(MovimientoBancarioSerializer(extracto.movimientos.all(), many=True).data)


class ImportarExtractoView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = ImportarExtractoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        extracto, errores = importar_extracto(
            archivo=data['archivo'],
            cuenta=data['cuenta_id'],
            saldo_inicial=data.get('saldo_inicial', Decimal('0')),
        )
        if extracto is None:
            return Response({'error': 'No se pudo importar el extracto', 'errores': errores}, status=400)
        return Response({
            'extracto_id': extracto.id,
            'movimientos': extracto.movimientos.count(),
            'errores': errores,
        }, status=status.HTTP_201_CREATED)


class MovimientoBancarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovimientoBancario.objects.select_related('extracto', 'asiento_contable').all()
    serializer_class = MovimientoBancarioSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['extracto', 'conciliado', 'tipo']

    @action(detail=True, methods=['post'])
    def conciliar(self, request, pk=None):
        movimiento = self.get_object()
        serializer = ConciliarManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movimiento.asiento_contable = serializer.validated_data['asiento_id']
        movimiento.conciliado = True
        movimiento.save(update_fields=['asiento_contable', 'conciliado'])
        return Response(MovimientoBancarioSerializer(movimiento).data)

    @action(detail=True, methods=['post'])
    def desconciliar(self, request, pk=None):
        movimiento = self.get_object()
        movimiento.asiento_contable = None
        movimiento.conciliado = False
        movimiento.save(update_fields=['asiento_contable', 'conciliado'])
        return Response(MovimientoBancarioSerializer(movimiento).data)


class ConciliacionBancariaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = ConciliacionBancaria.objects.select_related('cuenta', 'extracto').prefetch_related('partidas').all()
    serializer_class = ConciliacionBancariaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cuenta', 'estado']

    def create(self, request, *args, **kwargs):
        serializer = CrearConciliacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        extracto = serializer.validated_data['extracto']
        notas = serializer.validated_data.get('notas', '')
        cuenta = extracto.cuenta

        saldo_libros = calcular_saldo_libros(cuenta, extracto.periodo_inicio, extracto.periodo_fin)
        saldo_extracto = extracto.saldo_final_extracto
        diferencia = (saldo_extracto - saldo_libros).quantize(Decimal('0.01'))

        conciliacion = ConciliacionBancaria.objects.create(
            cuenta=cuenta,
            extracto=extracto,
            periodo=extracto.periodo_fin,
            saldo_extracto=saldo_extracto,
            saldo_libros=saldo_libros,
            diferencia=diferencia,
            notas=notas,
        )
        return Response(
            ConciliacionBancariaSerializer(conciliacion).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='conciliar-automatico')
    def conciliar_automatico_action(self, request, pk=None):
        conciliacion = self.get_object()
        cantidad = conciliar_automatico(conciliacion.extracto)
        return Response({'conciliados': cantidad})

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        conciliacion = self.get_object()
        reporte = generar_reporte_conciliacion(conciliacion)
        if reporte['diferencia_final'] != 0:
            return Response(
                {'detail': 'No se puede finalizar una conciliación con diferencia distinta de cero'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        conciliacion.diferencia = reporte['diferencia_final']
        conciliacion.estado = 'finalizada'
        conciliacion.finalizada_at = timezone.now()
        conciliacion.save(update_fields=['diferencia', 'estado', 'finalizada_at'])
        return Response(ConciliacionBancariaSerializer(conciliacion).data)

    @action(detail=True, methods=['get'])
    def reporte(self, request, pk=None):
        conciliacion = self.get_object()
        reporte = generar_reporte_conciliacion(conciliacion)
        if request.query_params.get('formato') == 'pdf':
            from apps.core.pdf_utils import render_pdf, pdf_response
            pdf_bytes = render_pdf('pdf/conciliacion_bancaria.html', {
                'conciliacion': conciliacion,
                'reporte': reporte,
                'usuario': request.user,
            }, base_url=request.build_absolute_uri('/'))
            return pdf_response(
                pdf_bytes,
                f'conciliacion_{conciliacion.cuenta.numero_cuenta}_{conciliacion.periodo}.pdf'
            )
        return Response(reporte)

    @action(detail=True, methods=['get', 'post'])
    def partidas(self, request, pk=None):
        conciliacion = self.get_object()
        if request.method == 'POST':
            serializer = PartidaConciliacionSerializer(data={**request.data, 'conciliacion': conciliacion.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(PartidaConciliacionSerializer(conciliacion.partidas.all(), many=True).data)


class PartidaConciliacionViewSet(viewsets.ModelViewSet):
    queryset = PartidaConciliacion.objects.select_related('conciliacion').all()
    serializer_class = PartidaConciliacionSerializer
    http_method_names = ['get', 'put', 'patch', 'delete']

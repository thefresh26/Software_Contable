import datetime
from decimal import Decimal
from django.db.models import Sum, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.empresas.mixins import EmpresaFilterMixin
from .models import CuentaPorCobrar, CuentaPorPagar, PagoRecibido, PagoRealizado
from .serializers import (
    CuentaPorCobrarSerializer, CuentaPorPagarSerializer,
    PagoRecibidoSerializer, PagoRealizadoSerializer, RegistrarPagoSerializer
)


class CuentaPorCobrarViewSet(EmpresaFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = CuentaPorCobrar.objects.select_related('factura', 'tercero').prefetch_related('pagos').all()
    serializer_class = CuentaPorCobrarSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado', 'tercero']

    def get_queryset(self):
        qs = super().get_queryset()
        # Actualizar estados vencidos antes de listar
        hoy = datetime.date.today()
        qs.filter(estado='pendiente', fecha_vencimiento__lt=hoy).update(estado='vencida')
        venc_desde = self.request.query_params.get('venc_desde')
        venc_hasta = self.request.query_params.get('venc_hasta')
        if venc_desde:
            qs = qs.filter(fecha_vencimiento__gte=venc_desde)
        if venc_hasta:
            qs = qs.filter(fecha_vencimiento__lte=venc_hasta)
        return qs

    @action(detail=True, methods=['post'], url_path='registrar-pago')
    def registrar_pago(self, request, pk=None):
        cuenta = self.get_object()
        if cuenta.estado == 'pagada':
            return Response({'error': 'Esta cuenta ya está pagada.'}, status=400)
        ser = RegistrarPagoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if data['valor'] > cuenta.valor_pendiente:
            return Response({'error': f'El valor excede el pendiente ({cuenta.valor_pendiente}).'}, status=400)
        pago = PagoRecibido.objects.create(cuenta_cobrar=cuenta, **data)
        return Response(PagoRecibidoSerializer(pago).data, status=201)

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        hoy = datetime.date.today()
        total_cobrar = CuentaPorCobrar.objects.exclude(estado='pagada').aggregate(s=Sum('valor_pendiente'))['s'] or 0
        total_pagar = CuentaPorPagar.objects.exclude(estado='pagada').aggregate(s=Sum('valor_pendiente'))['s'] or 0
        vencido_cobrar = CuentaPorCobrar.objects.filter(estado='vencida').aggregate(s=Sum('valor_pendiente'))['s'] or 0
        vencido_pagar = CuentaPorPagar.objects.filter(estado='vencida').aggregate(s=Sum('valor_pendiente'))['s'] or 0
        proximos_cobrar = list(
            CuentaPorCobrar.objects.filter(
                estado__in=['pendiente', 'parcial'],
                fecha_vencimiento__lte=hoy + datetime.timedelta(days=30)
            ).select_related('tercero', 'factura').values(
                'id', 'factura__numero', 'tercero__nombre', 'valor_pendiente', 'fecha_vencimiento', 'estado'
            )[:10]
        )
        return Response({
            'total_por_cobrar': total_cobrar,
            'total_por_pagar': total_pagar,
            'vencido_por_cobrar': vencido_cobrar,
            'vencido_por_pagar': vencido_pagar,
            'proximos_vencimientos_cobrar': proximos_cobrar,
        })


class CuentaPorPagarViewSet(EmpresaFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = CuentaPorPagar.objects.select_related('factura', 'tercero').prefetch_related('pagos').all()
    serializer_class = CuentaPorPagarSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado', 'tercero']

    def get_queryset(self):
        qs = super().get_queryset()
        hoy = datetime.date.today()
        qs.filter(estado='pendiente', fecha_vencimiento__lt=hoy).update(estado='vencida')
        venc_desde = self.request.query_params.get('venc_desde')
        venc_hasta = self.request.query_params.get('venc_hasta')
        if venc_desde:
            qs = qs.filter(fecha_vencimiento__gte=venc_desde)
        if venc_hasta:
            qs = qs.filter(fecha_vencimiento__lte=venc_hasta)
        return qs

    @action(detail=True, methods=['post'], url_path='registrar-pago')
    def registrar_pago(self, request, pk=None):
        cuenta = self.get_object()
        if cuenta.estado == 'pagada':
            return Response({'error': 'Esta cuenta ya está pagada.'}, status=400)
        ser = RegistrarPagoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if data['valor'] > cuenta.valor_pendiente:
            return Response({'error': f'El valor excede el pendiente ({cuenta.valor_pendiente}).'}, status=400)
        pago = PagoRealizado.objects.create(cuenta_pagar=cuenta, **data)
        return Response(PagoRealizadoSerializer(pago).data, status=201)

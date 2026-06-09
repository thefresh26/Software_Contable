from decimal import Decimal
import datetime
from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.empresas.mixins import EmpresaFilterMixin
from .models import Cotizacion, Presupuesto
from .serializers import (
    CotizacionSerializer, CotizacionCreateSerializer,
    PresupuestoSerializer, PresupuestoCreateSerializer,
)


class CotizacionViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Cotizacion.objects.select_related('tercero').prefetch_related('detalles__producto').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado']
    search_fields = ['numero', 'tercero__nombre']
    ordering = ['-fecha']

    def get_serializer_class(self):
        return CotizacionCreateSerializer if self.action == 'create' else CotizacionSerializer

    def create(self, request, *args, **kwargs):
        serializer = CotizacionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cot = serializer.save(empresa=getattr(request, 'empresa_activa', None))
        return Response(
            CotizacionSerializer(self.get_queryset().get(pk=cot.pk)).data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        qs = super().get_queryset()
        desde = self.request.query_params.get('fecha_desde')
        hasta = self.request.query_params.get('fecha_hasta')
        if desde:
            qs = qs.filter(fecha__gte=desde)
        if hasta:
            qs = qs.filter(fecha__lte=hasta)
        return qs

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        cot = self.get_object()
        if cot.estado not in ('borrador', 'enviada'):
            return Response({'error': 'Solo se pueden aprobar cotizaciones en borrador o enviadas.'}, status=400)
        cot.estado = 'aprobada'
        cot.save(update_fields=['estado'])
        return Response(CotizacionSerializer(cot).data)

    @action(detail=True, methods=['post'], url_path='convertir-factura')
    def convertir_factura(self, request, pk=None):
        from apps.facturacion.models import Factura, DetalleFactura
        from apps.facturacion.serializers import FacturaSerializer
        cot = self.get_object()
        if cot.estado != 'aprobada':
            return Response({'error': 'Solo se pueden convertir cotizaciones aprobadas.'}, status=400)
        with transaction.atomic():
            factura = Factura.objects.create(
                tipo='FV',
                tercero=cot.tercero,
                fecha=datetime.date.today(),
                fecha_vencimiento=cot.fecha_vencimiento,
                observaciones=f'Generada desde cotización {cot.numero}. {cot.observaciones}',
            )
            for det in cot.detalles.all():
                DetalleFactura.objects.create(
                    factura=factura,
                    producto=det.producto,
                    descripcion=det.descripcion,
                    cantidad=det.cantidad,
                    precio_unitario=det.precio_unitario,
                    iva_porcentaje=det.iva_porcentaje,
                )
            factura.recalcular_totales()
            cot.estado = 'aprobada'
            cot.save(update_fields=['estado'])
        return Response(FacturaSerializer(factura).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        from apps.core.pdf_utils import render_pdf, pdf_response
        cot = self.get_object()
        pdf_bytes = render_pdf('pdf/cotizacion.html', {
            'cotizacion': cot,
            'usuario': request.user,
            'detalles': cot.detalles.all(),
        }, base_url=request.build_absolute_uri('/'))
        return pdf_response(pdf_bytes, f'cotizacion_{cot.numero}.pdf')



class PresupuestoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Presupuesto.objects.prefetch_related('items__cuenta').all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado']

    def get_serializer_class(self):
        return PresupuestoCreateSerializer if self.action == 'create' else PresupuestoSerializer

    def create(self, request, *args, **kwargs):
        serializer = PresupuestoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pres = serializer.save(empresa=getattr(request, 'empresa_activa', None))
        return Response(
            PresupuestoSerializer(self.get_queryset().get(pk=pres.pk)).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'])
    def ejecucion(self, request, pk=None):
        from apps.contabilidad.models import MovimientoContable
        presupuesto = self.get_object()
        items = presupuesto.items.select_related('cuenta').all()
        resultado = []
        for item in items:
            movs = MovimientoContable.objects.filter(
                cuenta=item.cuenta,
                asiento__fecha__gte=presupuesto.periodo_inicio,
                asiento__fecha__lte=presupuesto.periodo_fin,
            )
            tipo = item.cuenta.tipo
            if tipo in ('activo', 'gasto', 'costo'):
                ejecutado = sum((m.debito - m.credito) for m in movs)
            else:
                ejecutado = sum((m.credito - m.debito) for m in movs)
            presupuestado = item.valor_presupuestado
            diferencia = presupuestado - ejecutado
            porcentaje = float(ejecutado / presupuestado * 100) if presupuestado else 0
            resultado.append({
                'cuenta_codigo': item.cuenta.codigo,
                'cuenta_nombre': item.cuenta.nombre,
                'descripcion': item.descripcion,
                'presupuestado': presupuestado,
                'ejecutado': ejecutado,
                'diferencia': diferencia,
                'porcentaje_ejecucion': round(porcentaje, 1),
            })
        total_presupuestado = sum(r['presupuestado'] for r in resultado)
        total_ejecutado = sum(r['ejecutado'] for r in resultado)
        return Response({
            'presupuesto': str(presupuesto),
            'periodo': f"{presupuesto.periodo_inicio} — {presupuesto.periodo_fin}",
            'items': resultado,
            'total_presupuestado': total_presupuestado,
            'total_ejecutado': total_ejecutado,
        })

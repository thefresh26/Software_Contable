from decimal import Decimal
from django.http import HttpResponse
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.empresas.mixins import EmpresaFilterMixin
from apps.core.excel_utils import nuevo_libro, ajustar_columnas, excel_response
from .models import Factura, DetalleFactura, TipoRetencion, MedioPago, Anticipo, AplicacionAnticipo, ResolucionDIAN
from .serializers import (
    FacturaSerializer, FacturaCreateSerializer, DetalleFacturaSerializer,
    TipoRetencionSerializer, RetencionFacturaSerializer, MedioPagoSerializer,
    AnticipoSerializer, AplicacionAnticipoSerializer, ResolucionDIANSerializer,
)
from .signals import (
    generar_asiento_factura_venta, generar_asiento_factura_compra,
    actualizar_stock_emision, revertir_stock_anulacion,
    crear_cuenta_cobrar, crear_cuenta_pagar, notificar_factura_emitida,
)


class TipoRetencionViewSet(viewsets.ModelViewSet):
    queryset = TipoRetencion.objects.all()
    serializer_class = TipoRetencionSerializer
    filterset_fields = ['tipo', 'activo']


class FacturaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Factura.objects.select_related('tercero').prefetch_related(
        'detalles__producto', 'retenciones__tipo_retencion', 'medios_pago'
    ).all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo', 'estado']
    search_fields = ['numero', 'tercero__nombre']
    ordering = ['-fecha', '-created_at']

    def get_serializer_class(self):
        return FacturaCreateSerializer if self.action == 'create' else FacturaSerializer

    def create(self, request, *args, **kwargs):
        serializer = FacturaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        factura = serializer.save(empresa=getattr(request, 'empresa_activa', None))
        return Response(
            FacturaSerializer(self.get_queryset().get(pk=factura.pk)).data,
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
    def emitir(self, request, pk=None):
        factura = self.get_object()
        if factura.estado != 'borrador':
            return Response({'error': 'Solo se pueden emitir facturas en borrador.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                actualizar_stock_emision(factura)
                if factura.tipo == 'FV':
                    generar_asiento_factura_venta(factura)
                    crear_cuenta_cobrar(factura)
                elif factura.tipo == 'FC':
                    generar_asiento_factura_compra(factura)
                    crear_cuenta_pagar(factura)
                factura.estado = 'emitida'
                factura.save(update_fields=['estado'])
                notificar_factura_emitida(factura)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FacturaSerializer(factura).data)

    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        factura = self.get_object()
        if factura.estado != 'emitida':
            return Response({'error': 'Solo se pueden anular facturas emitidas.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                revertir_stock_anulacion(factura)
                if hasattr(factura, 'asiento'):
                    factura.asiento.delete()
                factura.estado = 'anulada'
                factura.save(update_fields=['estado'])
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FacturaSerializer(factura).data)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        from apps.core.pdf_utils import render_pdf, pdf_response
        factura = self.get_object()
        pdf_bytes = render_pdf('pdf/factura.html', {
            'factura': factura,
            'usuario': request.user,
            'detalles': factura.detalles.select_related('producto').all(),
            'retenciones': factura.retenciones.select_related('tipo_retencion').all(),
        }, base_url=request.build_absolute_uri('/'))
        return pdf_response(pdf_bytes, f'factura_{factura.numero}.pdf')

    @action(detail=True, methods=['get'])
    def retenciones(self, request, pk=None):
        factura = self.get_object()
        return Response(RetencionFacturaSerializer(factura.retenciones.all(), many=True).data)

    @action(detail=True, methods=['get', 'post'], url_path='medios-pago')
    def medios_pago(self, request, pk=None):
        factura = self.get_object()
        if request.method == 'GET':
            return Response(MedioPagoSerializer(factura.medios_pago.all(), many=True).data)
        serializer = MedioPagoSerializer(data={**request.data, 'factura': factura.pk})
        serializer.is_valid(raise_exception=True)
        total_pagado = sum(m.valor for m in factura.medios_pago.all()) + serializer.validated_data['valor']
        if total_pagado > factura.total:
            return Response({'error': 'La suma de medios de pago supera el total de la factura.'}, status=400)
        medio = serializer.save()
        if total_pagado >= factura.total and factura.estado == 'emitida':
            factura.estado = 'pagada'
            factura.save(update_fields=['estado'])
        return Response(MedioPagoSerializer(medio).data, status=201)

    @action(detail=False, methods=['get'], url_path='exportar')
    def exportar(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        desde = request.query_params.get('fecha_desde', '')
        hasta = request.query_params.get('fecha_hasta', '')
        tipo = request.query_params.get('tipo', '')

        qs = self.get_queryset().select_related('tercero')
        if tipo:
            qs = qs.filter(tipo=tipo)
        if desde:
            qs = qs.filter(fecha__gte=desde)
        if hasta:
            qs = qs.filter(fecha__lte=hasta)

        cabeceras = ['Número', 'Tipo', 'Tercero', 'Fecha', 'Vencimiento', 'Subtotal', 'IVA', 'Total', 'Estado']
        wb, ws, fila = nuevo_libro('Facturas', empresa_nombre, 'Listado de Facturas', cabeceras)
        tipos = dict(Factura.TIPOS)
        estados = dict(Factura.ESTADOS)
        for f in qs:
            ws.append([
                f.numero, tipos.get(f.tipo, f.tipo), f.tercero.nombre,
                str(f.fecha), str(f.fecha_vencimiento or ''),
                float(f.subtotal), float(f.iva), float(f.total),
                estados.get(f.estado, f.estado),
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'facturas.xlsx')


class MedioPagoViewSet(viewsets.ModelViewSet):
    queryset = MedioPago.objects.select_related('factura').all()
    serializer_class = MedioPagoSerializer
    http_method_names = ['get', 'delete', 'head', 'options']


class DetalleFacturaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = DetalleFactura.objects.select_related('factura', 'producto').all()
    serializer_class = DetalleFacturaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['factura']


class AnticipoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Anticipo.objects.select_related('tercero').prefetch_related('aplicaciones').all()
    serializer_class = AnticipoSerializer
    filterset_fields = ['tipo', 'estado', 'tercero']

    def perform_create(self, serializer):
        serializer.save(empresa=getattr(self.request, 'empresa_activa', None))

    @action(detail=True, methods=['post'])
    def aplicar(self, request, pk=None):
        anticipo = self.get_object()
        if anticipo.estado != 'activo':
            return Response({'error': 'El anticipo no está activo.'}, status=400)
        factura_id = request.data.get('factura_id')
        valor = request.data.get('valor')
        if not factura_id or not valor:
            return Response({'error': 'Se requieren factura_id y valor.'}, status=400)
        valor = Decimal(str(valor))
        if valor > anticipo.valor_disponible:
            return Response({'error': f'Valor excede el disponible ({anticipo.valor_disponible}).'}, status=400)
        try:
            factura = Factura.objects.get(pk=factura_id)
        except Factura.DoesNotExist:
            return Response({'error': 'Factura no encontrada.'}, status=404)
        import datetime as dt
        aplicacion = AplicacionAnticipo.objects.create(
            anticipo=anticipo, factura=factura,
            valor_aplicado=valor, fecha=dt.date.today()
        )
        anticipo.valor_aplicado += valor
        anticipo.valor_disponible -= valor
        if anticipo.valor_disponible <= 0:
            anticipo.estado = 'aplicado'
        anticipo.save(update_fields=['valor_aplicado', 'valor_disponible', 'estado'])
        return Response(AplicacionAnticipoSerializer(aplicacion).data, status=201)

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        anticipo = self.get_object()
        if anticipo.estado == 'devuelto':
            return Response({'error': 'El anticipo ya fue devuelto.'}, status=400)
        anticipo.estado = 'devuelto'
        anticipo.save(update_fields=['estado'])
        return Response(AnticipoSerializer(anticipo).data)


class ResolucionDIANViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = ResolucionDIAN.objects.all()
    serializer_class = ResolucionDIANSerializer
    filterset_fields = ['activa', 'tipo']

    def perform_create(self, serializer):
        serializer.save(empresa=getattr(self.request, 'empresa_activa', None))

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        res = self.get_object()
        empresa = getattr(request, 'empresa_activa', None)
        ResolucionDIAN.objects.filter(empresa=empresa, tipo=res.tipo).update(activa=False)
        res.activa = True
        res.save(update_fields=['activa'])
        return Response(ResolucionDIANSerializer(res).data)

    @action(detail=False, methods=['get'])
    def activa(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        tipo = request.query_params.get('tipo', 'venta')
        res = ResolucionDIAN.objects.filter(empresa=empresa, activa=True, tipo=tipo).first()
        if not res:
            return Response({'error': 'No hay resolución activa.'}, status=404)
        return Response(ResolucionDIANSerializer(res).data)

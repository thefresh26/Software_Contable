from decimal import Decimal
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from apps.empresas.mixins import EmpresaFilterMixin
from .models import Empleado, LiquidacionNomina, calcular_nomina
from .serializers import (
    EmpleadoSerializer, LiquidacionNominaSerializer, LiquidarNominaSerializer
)


class EmpleadoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo', 'tipo_contrato', 'departamento']
    search_fields = ['nombre', 'cedula', 'cargo']


class LiquidacionNominaViewSet(EmpresaFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = LiquidacionNomina.objects.select_related('empleado').all()
    serializer_class = LiquidacionNominaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['empleado', 'estado']

    def get_queryset(self):
        qs = super().get_queryset()
        mes = self.request.query_params.get('mes')
        año = self.request.query_params.get('año')
        if mes:
            qs = qs.filter(periodo_inicio__month=mes)
        if año:
            qs = qs.filter(periodo_inicio__year=año)
        return qs

    @action(detail=True, methods=['get'])
    def colilla(self, request, pk=None):
        from apps.core.pdf_utils import render_pdf, pdf_response
        liquidacion = self.get_object()
        pdf_bytes = render_pdf('pdf/colilla_nomina.html', {
            'liquidacion': liquidacion,
            'usuario': request.user,
            'empleado': liquidacion.empleado,
        }, base_url=request.build_absolute_uri('/'))
        return pdf_response(
            pdf_bytes,
            f'colilla_{liquidacion.empleado.cedula}_{liquidacion.periodo_fin}.pdf'
        )

    @action(detail=False, methods=['get'], url_path='resumen-mes')
    def resumen_mes(self, request):
        mes = request.query_params.get('mes')
        año = request.query_params.get('año')
        qs = LiquidacionNomina.objects.all()
        if mes:
            qs = qs.filter(periodo_inicio__month=mes)
        if año:
            qs = qs.filter(periodo_inicio__year=año)
        totales = qs.aggregate(
            total_devengado=Sum('total_devengado'),
            total_deducido=Sum('total_deducido'),
            neto_pagar=Sum('neto_pagar'),
            salud_empresa=Sum('salud_empresa'),
            pension_empresa=Sum('pension_empresa'),
            arl=Sum('arl'),
            caja_compensacion=Sum('caja_compensacion'),
            sena=Sum('sena'),
            icbf=Sum('icbf'),
        )
        totales['cantidad_liquidaciones'] = qs.count()
        return Response(totales)


class LiquidarNominaView(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def liquidar(self, request):
        serializer = LiquidarNominaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        empleado = data['empleado']
        periodo_inicio = data['periodo_inicio']
        periodo_fin = data['periodo_fin']

        if LiquidacionNomina.objects.filter(
            empleado=empleado,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        ).exists():
            return Response(
                {
                    'detail': (
                        f"Ya existe una liquidación para este empleado en el "
                        f"período {periodo_inicio.month}/{periodo_inicio.year}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        calculo = calcular_nomina(
            empleado=empleado,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            bonificaciones=data.get('bonificaciones', Decimal('0')),
            horas_extra_diurnas=data.get('horas_extra_diurnas', Decimal('0')),
            horas_extra_nocturnas=data.get('horas_extra_nocturnas', Decimal('0')),
            retencion_fuente=data.get('retencion_fuente', Decimal('0')),
            otras_deducciones=data.get('otras_deducciones', Decimal('0')),
        )

        liquidacion = LiquidacionNomina.objects.create(
            empleado=empleado,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            empresa=getattr(request, 'empresa_activa', None),
            **calculo,
        )
        return Response(
            LiquidacionNominaSerializer(liquidacion).data,
            status=status.HTTP_201_CREATED,
        )

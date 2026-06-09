from decimal import Decimal
from django.db.models import Sum, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from apps.empresas.mixins import EmpresaFilterMixin
from .models import CuentaPUC, AsientoContable, MovimientoContable, CentroCosto
from .serializers import (
    CuentaPUCSerializer, AsientoContableSerializer,
    AsientoContableCreateSerializer, CentroCostoSerializer,
)


class CentroCostoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = CentroCosto.objects.select_related('padre').all()
    serializer_class = CentroCostoSerializer
    filterset_fields = ['activo']

    @action(detail=True, methods=['get'])
    def movimientos(self, request, pk=None):
        centro = self.get_object()
        desde = request.query_params.get('desde')
        hasta = request.query_params.get('hasta')
        qs = MovimientoContable.objects.filter(centro_costo=centro).select_related('asiento', 'cuenta')
        if desde:
            qs = qs.filter(asiento__fecha__gte=desde)
        if hasta:
            qs = qs.filter(asiento__fecha__lte=hasta)
        from .serializers import MovimientoContableSerializer
        return Response(MovimientoContableSerializer(qs.order_by('asiento__fecha'), many=True).data)


class CuentaPUCViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = CuentaPUC.objects.select_related('padre').all()
    serializer_class = CuentaPUCSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['tipo', 'nivel', 'activa', 'permite_movimiento']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']


class AsientoContableViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = AsientoContable.objects.prefetch_related('movimientos__cuenta').all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['es_manual']

    def get_serializer_class(self):
        return AsientoContableCreateSerializer if self.action == 'create' else AsientoContableSerializer

    def create(self, request, *args, **kwargs):
        serializer = AsientoContableCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asiento = serializer.save(empresa=getattr(request, 'empresa_activa', None))
        return Response(
            AsientoContableSerializer(self.get_queryset().get(pk=asiento.pk)).data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        qs = super().get_queryset()
        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')
        if desde:
            qs = qs.filter(fecha__gte=desde)
        if hasta:
            qs = qs.filter(fecha__lte=hasta)
        return qs

    @action(detail=False, methods=['get'], url_path='balance-general')
    def balance_general(self, request):
        fecha = request.query_params.get('fecha')
        qs = MovimientoContable.objects.select_related('cuenta', 'asiento')
        if fecha:
            qs = qs.filter(asiento__fecha__lte=fecha)

        resultado = {}
        for mov in qs:
            cuenta = mov.cuenta
            tipo = cuenta.tipo
            if tipo not in resultado:
                resultado[tipo] = Decimal('0')
            if tipo in ('activo', 'gasto', 'costo'):
                resultado[tipo] += mov.debito - mov.credito
            else:
                resultado[tipo] += mov.credito - mov.debito

        activos = resultado.get('activo', Decimal('0'))
        pasivos = resultado.get('pasivo', Decimal('0'))
        # La utilidad del ejercicio (ingresos - costos - gastos) hace parte del
        # patrimonio hasta que se registre el cierre contable de fin de período.
        utilidad_ejercicio = (
            resultado.get('ingreso', Decimal('0'))
            - resultado.get('costo', Decimal('0'))
            - resultado.get('gasto', Decimal('0'))
        )
        patrimonio = resultado.get('patrimonio', Decimal('0')) + utilidad_ejercicio
        return Response({
            'activos': activos,
            'pasivos': pasivos,
            'patrimonio': patrimonio,
            'utilidad_ejercicio': utilidad_ejercicio,
            'cuadrado': activos == (pasivos + patrimonio),
        })

    @action(detail=False, methods=['get'], url_path='estado-resultados')
    def estado_resultados(self, request):
        desde = request.query_params.get('desde')
        hasta = request.query_params.get('hasta')
        qs = MovimientoContable.objects.select_related('cuenta', 'asiento')
        if desde:
            qs = qs.filter(asiento__fecha__gte=desde)
        if hasta:
            qs = qs.filter(asiento__fecha__lte=hasta)

        ingresos = Decimal('0')
        costos = Decimal('0')
        gastos = Decimal('0')
        for mov in qs:
            tipo = mov.cuenta.tipo
            if tipo == 'ingreso':
                ingresos += mov.credito - mov.debito
            elif tipo == 'costo':
                costos += mov.debito - mov.credito
            elif tipo == 'gasto':
                gastos += mov.debito - mov.credito

        utilidad_bruta = ingresos - costos
        utilidad_neta = utilidad_bruta - gastos
        return Response({
            'ingresos': ingresos,
            'costos': costos,
            'gastos': gastos,
            'utilidad_bruta': utilidad_bruta,
            'utilidad_neta': utilidad_neta,
        })

    @action(detail=False, methods=['get'], url_path='libro-diario')
    def libro_diario(self, request):
        desde = request.query_params.get('desde')
        hasta = request.query_params.get('hasta')
        qs = AsientoContable.objects.prefetch_related('movimientos__cuenta').order_by('fecha')
        if desde:
            qs = qs.filter(fecha__gte=desde)
        if hasta:
            qs = qs.filter(fecha__lte=hasta)
        from .serializers import AsientoContableSerializer
        return Response(AsientoContableSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='libro-mayor')
    def libro_mayor(self, request):
        codigo = request.query_params.get('cuenta')
        desde = request.query_params.get('desde')
        hasta = request.query_params.get('hasta')
        if not codigo:
            return Response({'error': 'Parámetro cuenta requerido.'}, status=400)
        try:
            cuenta = CuentaPUC.objects.get(codigo=codigo)
        except CuentaPUC.DoesNotExist:
            return Response({'error': 'Cuenta no encontrada.'}, status=404)

        qs = MovimientoContable.objects.filter(cuenta=cuenta).select_related('asiento')
        if desde:
            qs = qs.filter(asiento__fecha__gte=desde)
        if hasta:
            qs = qs.filter(asiento__fecha__lte=hasta)
        qs = qs.order_by('asiento__fecha')

        movimientos = []
        saldo = Decimal('0')
        for mov in qs:
            if cuenta.tipo in ('activo', 'gasto', 'costo'):
                saldo += mov.debito - mov.credito
            else:
                saldo += mov.credito - mov.debito
            movimientos.append({
                'fecha': mov.asiento.fecha,
                'descripcion': mov.descripcion or mov.asiento.descripcion,
                'debito': mov.debito,
                'credito': mov.credito,
                'saldo': saldo,
            })
        return Response({'cuenta': str(cuenta), 'movimientos': movimientos})

    @action(detail=False, methods=['get'], url_path='balance-comprobacion')
    def balance_comprobacion(self, request):
        desde = request.query_params.get('desde')
        hasta = request.query_params.get('hasta')
        qs = MovimientoContable.objects.select_related('cuenta', 'asiento')
        if desde:
            qs = qs.filter(asiento__fecha__gte=desde)
        if hasta:
            qs = qs.filter(asiento__fecha__lte=hasta)

        cuentas = {}
        for mov in qs:
            c = mov.cuenta
            if c.codigo not in cuentas:
                cuentas[c.codigo] = {
                    'codigo': c.codigo,
                    'nombre': c.nombre,
                    'tipo': c.tipo,
                    'debito': Decimal('0'),
                    'credito': Decimal('0'),
                }
            cuentas[c.codigo]['debito'] += mov.debito
            cuentas[c.codigo]['credito'] += mov.credito

        filas = sorted(cuentas.values(), key=lambda x: x['codigo'])
        total_debito = sum(f['debito'] for f in filas)
        total_credito = sum(f['credito'] for f in filas)
        return Response({
            'filas': filas,
            'total_debito': total_debito,
            'total_credito': total_credito,
            'cuadrado': total_debito == total_credito,
        })

    @action(detail=False, methods=['get'], url_path='por-centro')
    def por_centro(self, request):
        desde = request.query_params.get('desde')
        hasta = request.query_params.get('hasta')
        qs = MovimientoContable.objects.select_related('cuenta', 'asiento', 'centro_costo')
        if desde:
            qs = qs.filter(asiento__fecha__gte=desde)
        if hasta:
            qs = qs.filter(asiento__fecha__lte=hasta)

        centros: dict = {}
        for mov in qs:
            clave = mov.centro_costo.codigo if mov.centro_costo else 'SIN CENTRO'
            nombre = mov.centro_costo.nombre if mov.centro_costo else 'Sin Centro de Costo'
            if clave not in centros:
                centros[clave] = {'codigo': clave, 'nombre': nombre,
                                  'ingresos': Decimal('0'), 'gastos': Decimal('0'), 'costos': Decimal('0')}
            tipo = mov.cuenta.tipo
            if tipo == 'ingreso':
                centros[clave]['ingresos'] += mov.credito - mov.debito
            elif tipo == 'gasto':
                centros[clave]['gastos'] += mov.debito - mov.credito
            elif tipo == 'costo':
                centros[clave]['costos'] += mov.debito - mov.credito

        resultado = []
        for c in sorted(centros.values(), key=lambda x: x['codigo']):
            c['utilidad'] = c['ingresos'] - c['gastos'] - c['costos']
            resultado.append(c)
        return Response(resultado)

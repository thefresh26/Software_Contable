from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

import datetime
from rest_framework.views import APIView

from apps.empresas.mixins import EmpresaFilterMixin
from apps.core.excel_utils import nuevo_libro, ajustar_columnas, excel_response
from .models import CuentaPUC, AsientoContable, MovimientoContable, CentroCosto, CierrePeriodo, FlujoCaja
from .serializers import (
    CuentaPUCSerializer, AsientoContableSerializer,
    AsientoContableCreateSerializer, CentroCostoSerializer, CierrePeriodoSerializer,
    FlujoCajaSerializer,
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

    @action(detail=False, methods=['get'], url_path='exportar-balance-general')
    def exportar_balance_general(self, request):
        fecha = request.query_params.get('fecha', str(timezone.now().date()))
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'

        qs = MovimientoContable.objects.select_related('cuenta', 'asiento')
        if empresa:
            qs = qs.filter(asiento__empresa=empresa)
        qs = qs.filter(asiento__fecha__lte=fecha)

        totales: dict = {}
        for mov in qs:
            tipo = mov.cuenta.tipo
            totales.setdefault(tipo, Decimal('0'))
            if tipo in ('activo', 'gasto', 'costo'):
                totales[tipo] += mov.debito - mov.credito
            else:
                totales[tipo] += mov.credito - mov.debito

        activos = totales.get('activo', Decimal('0'))
        pasivos = totales.get('pasivo', Decimal('0'))
        utilidad = totales.get('ingreso', Decimal('0')) - totales.get('costo', Decimal('0')) - totales.get('gasto', Decimal('0'))
        patrimonio = totales.get('patrimonio', Decimal('0')) + utilidad

        cabeceras = ['Sección', 'Valor (COP)']
        wb, ws, fila = nuevo_libro('Balance General', empresa_nombre, f'Balance General al {fecha}', cabeceras)
        filas_data = [
            ('ACTIVOS', float(activos)),
            ('PASIVOS', float(pasivos)),
            ('Utilidad del ejercicio', float(utilidad)),
            ('PATRIMONIO TOTAL', float(patrimonio)),
            ('Pasivos + Patrimonio', float(pasivos + patrimonio)),
        ]
        for row in filas_data:
            ws.append(row)
        ajustar_columnas(ws)
        return excel_response(wb, f'balance_general_{fecha}.xlsx')

    @action(detail=False, methods=['get'], url_path='exportar-estado-resultados')
    def exportar_estado_resultados(self, request):
        desde = request.query_params.get('desde', '')
        hasta = request.query_params.get('hasta', str(timezone.now().date()))
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'

        qs = MovimientoContable.objects.select_related('cuenta', 'asiento')
        if empresa:
            qs = qs.filter(asiento__empresa=empresa)
        if desde:
            qs = qs.filter(asiento__fecha__gte=desde)
        if hasta:
            qs = qs.filter(asiento__fecha__lte=hasta)

        ingresos = costos = gastos = Decimal('0')
        for mov in qs:
            tipo = mov.cuenta.tipo
            if tipo == 'ingreso':
                ingresos += mov.credito - mov.debito
            elif tipo == 'costo':
                costos += mov.debito - mov.credito
            elif tipo == 'gasto':
                gastos += mov.debito - mov.credito

        cabeceras = ['Concepto', 'Valor (COP)']
        periodo = f"{desde} — {hasta}" if desde else f"Al {hasta}"
        wb, ws, fila = nuevo_libro('Estado de Resultados', empresa_nombre, f'Estado de Resultados {periodo}', cabeceras)
        for row in [
            ('INGRESOS OPERACIONALES', float(ingresos)),
            ('(-) COSTOS DE VENTAS', float(costos)),
            ('UTILIDAD BRUTA', float(ingresos - costos)),
            ('(-) GASTOS OPERACIONALES', float(gastos)),
            ('UTILIDAD NETA', float(ingresos - costos - gastos)),
        ]:
            ws.append(row)
        ajustar_columnas(ws)
        return excel_response(wb, f'estado_resultados.xlsx')

    @action(detail=False, methods=['get'], url_path='exportar-libro-diario')
    def exportar_libro_diario(self, request):
        desde = request.query_params.get('desde', '')
        hasta = request.query_params.get('hasta', str(timezone.now().date()))
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'

        qs = AsientoContable.objects.prefetch_related('movimientos__cuenta').order_by('fecha')
        if empresa:
            qs = qs.filter(empresa=empresa)
        if desde:
            qs = qs.filter(fecha__gte=desde)
        if hasta:
            qs = qs.filter(fecha__lte=hasta)

        cabeceras = ['Fecha', 'Asiento #', 'Descripción', 'Cuenta', 'Débito', 'Crédito']
        wb, ws, fila = nuevo_libro('Libro Diario', empresa_nombre, f'Libro Diario {desde} — {hasta}', cabeceras)
        for asiento in qs:
            for mov in asiento.movimientos.all():
                ws.append([
                    str(asiento.fecha), asiento.pk, asiento.descripcion[:60],
                    f"{mov.cuenta.codigo} — {mov.cuenta.nombre}",
                    float(mov.debito), float(mov.credito),
                ])
        ajustar_columnas(ws)
        return excel_response(wb, 'libro_diario.xlsx')

    @action(detail=False, methods=['get'], url_path='exportar-libro-mayor')
    def exportar_libro_mayor(self, request):
        codigo = request.query_params.get('cuenta', '')
        desde = request.query_params.get('desde', '')
        hasta = request.query_params.get('hasta', str(timezone.now().date()))
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'

        qs = MovimientoContable.objects.select_related('cuenta', 'asiento').order_by('asiento__fecha')
        if empresa:
            qs = qs.filter(asiento__empresa=empresa)
        if codigo:
            qs = qs.filter(cuenta__codigo=codigo)
        if desde:
            qs = qs.filter(asiento__fecha__gte=desde)
        if hasta:
            qs = qs.filter(asiento__fecha__lte=hasta)

        cabeceras = ['Fecha', 'Cuenta', 'Descripción', 'Débito', 'Crédito', 'Saldo']
        wb, ws, fila = nuevo_libro('Libro Mayor', empresa_nombre, f'Libro Mayor {codigo}', cabeceras)
        saldo = Decimal('0')
        for mov in qs:
            tipo = mov.cuenta.tipo
            if tipo in ('activo', 'gasto', 'costo'):
                saldo += mov.debito - mov.credito
            else:
                saldo += mov.credito - mov.debito
            ws.append([
                str(mov.asiento.fecha),
                f"{mov.cuenta.codigo} — {mov.cuenta.nombre}",
                mov.descripcion or mov.asiento.descripcion[:50],
                float(mov.debito), float(mov.credito), float(saldo),
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'libro_mayor.xlsx')


class CierrePeriodoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = CierrePeriodo.objects.select_related('cerrado_por', 'empresa').all()
    serializer_class = CierrePeriodoSerializer
    filterset_fields = ['estado']

    def perform_create(self, serializer):
        serializer.save(empresa=getattr(self.request, 'empresa_activa', None))

    @action(detail=False, methods=['get'], url_path='estado')
    def estado_periodo(self, request):
        fecha_str = request.query_params.get('fecha', str(timezone.now().date()))
        try:
            import datetime
            fecha = datetime.date.fromisoformat(fecha_str)
        except ValueError:
            return Response({'error': 'Fecha inválida. Use YYYY-MM-DD.'}, status=400)
        primer_dia = fecha.replace(day=1)
        empresa = getattr(request, 'empresa_activa', None)
        cierre = CierrePeriodo.objects.filter(empresa=empresa, periodo=primer_dia).first()
        return Response({
            'periodo': str(primer_dia),
            'cerrado': cierre.estado == 'cerrado' if cierre else False,
            'cierre_id': cierre.pk if cierre else None,
        })

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        cierre = self.get_object()
        if cierre.estado == 'cerrado':
            return Response({'error': 'El período ya está cerrado.'}, status=400)
        cierre.estado = 'cerrado'
        cierre.cerrado_por = request.user
        cierre.cerrado_at = timezone.now()
        cierre.save()
        return Response(CierrePeriodoSerializer(cierre).data)

    @action(detail=True, methods=['post'])
    def reabrir(self, request, pk=None):
        if not (request.user.is_superuser or getattr(request.user, 'rol', '') == 'admin'):
            return Response({'error': 'Solo un administrador puede reabrir un período.'}, status=403)
        cierre = self.get_object()
        if cierre.estado == 'abierto':
            return Response({'error': 'El período ya está abierto.'}, status=400)
        cierre.estado = 'abierto'
        cierre.cerrado_por = None
        cierre.cerrado_at = None
        cierre.save()
        return Response(CierrePeriodoSerializer(cierre).data)


class FlujoCajaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = FlujoCaja.objects.select_related('cuenta_bancaria', 'factura').all()
    serializer_class = FlujoCajaSerializer
    filterset_fields = ['tipo', 'es_proyectado', 'cuenta_bancaria']

    def perform_create(self, serializer):
        serializer.save(empresa=getattr(self.request, 'empresa_activa', None))

    def get_queryset(self):
        qs = super().get_queryset()
        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')
        if desde:
            qs = qs.filter(fecha__gte=desde)
        if hasta:
            qs = qs.filter(fecha__lte=hasta)
        return qs

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        qs = FlujoCaja.objects.filter(empresa=empresa)
        ingresos = qs.filter(tipo='ingreso').aggregate(s=Sum('valor'))['s'] or Decimal('0')
        egresos = qs.filter(tipo='egreso').aggregate(s=Sum('valor'))['s'] or Decimal('0')
        return Response({
            'total_ingresos': ingresos,
            'total_egresos': egresos,
            'saldo': ingresos - egresos,
        })

    @action(detail=False, methods=['get'])
    def proyeccion(self, request):
        meses = int(request.query_params.get('meses', 3))
        empresa = getattr(request, 'empresa_activa', None)
        hoy = datetime.date.today()
        resultado = []
        for i in range(meses):
            mes = hoy.month + i
            year = hoy.year + (mes - 1) // 12
            mes = ((mes - 1) % 12) + 1
            primer_dia = datetime.date(year, mes, 1)
            import calendar
            ultimo_dia = datetime.date(year, mes, calendar.monthrange(year, mes)[1])
            qs = FlujoCaja.objects.filter(empresa=empresa, fecha__range=[primer_dia, ultimo_dia])
            ingresos = qs.filter(tipo='ingreso').aggregate(s=Sum('valor'))['s'] or Decimal('0')
            egresos = qs.filter(tipo='egreso').aggregate(s=Sum('valor'))['s'] or Decimal('0')
            resultado.append({
                'mes': primer_dia.strftime('%Y-%m'),
                'ingresos': ingresos,
                'egresos': egresos,
                'saldo': ingresos - egresos,
            })
        return Response(resultado)

    @action(detail=False, methods=['get'], url_path='exportar')
    def exportar(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        qs = self.get_queryset()
        cabeceras = ['Fecha', 'Tipo', 'Concepto', 'Valor', 'Cuenta', 'Proyectado']
        wb, ws, _ = nuevo_libro('Flujo de Caja', empresa_nombre, 'Flujo de Caja', cabeceras)
        for f in qs:
            ws.append([
                str(f.fecha), f.get_tipo_display(), f.concepto, float(f.valor),
                f.cuenta_bancaria.nombre if f.cuenta_bancaria else '',
                'Sí' if f.es_proyectado else 'No',
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'flujo_caja.xlsx')


# ── Modelos disponibles para Reportes Personalizables ─────────────────────────
_MODELOS_REPORTE = {
    'facturas': ('apps.facturacion.models', 'Factura'),
    'terceros': ('apps.terceros.models', 'Tercero'),
    'movimientos': ('apps.contabilidad.models', 'MovimientoContable'),
    'productos': ('apps.inventario.models', 'Producto'),
    'empleados': ('apps.nomina.models', 'Empleado'),
}


class ReportePersonalizadoView(APIView):
    def post(self, request):
        config = request.data
        modelo_key = config.get('modelo', '')
        campos = config.get('campos', [])
        filtros = config.get('filtros', {})
        formato = config.get('formato', 'json')
        empresa = getattr(request, 'empresa_activa', None)

        if modelo_key not in _MODELOS_REPORTE:
            return Response({'error': f'Modelo no válido. Opciones: {list(_MODELOS_REPORTE)}'}, status=400)

        import importlib
        modulo_nombre, clase_nombre = _MODELOS_REPORTE[modelo_key]
        modulo = importlib.import_module(modulo_nombre)
        Modelo = getattr(modulo, clase_nombre)

        qs = Modelo.objects.all()
        if hasattr(Modelo, 'empresa'):
            qs = qs.filter(empresa=empresa)

        # Filtros dinámicos
        filtros_validos = {}
        for campo, valor in filtros.items():
            if valor not in ('', None):
                filtros_validos[campo] = valor
        if filtros_validos:
            try:
                qs = qs.filter(**filtros_validos)
            except Exception:
                pass

        # Limitar preview
        if formato == 'json':
            qs = qs[:10]
            datos = list(qs.values(*campos) if campos else qs.values())
            return Response({'modelo': modelo_key, 'campos': campos, 'datos': datos, 'total': len(datos)})

        # Excel
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        cabeceras = campos if campos else [f.name for f in Modelo._meta.get_fields() if hasattr(f, 'name')][:10]
        wb, ws, _ = nuevo_libro('Reporte', empresa_nombre, f'Reporte {modelo_key}', cabeceras)
        for obj in qs.values(*cabeceras):
            ws.append([str(obj.get(c, '')) for c in cabeceras])
        ajustar_columnas(ws)
        return excel_response(wb, f'reporte_{modelo_key}.xlsx')

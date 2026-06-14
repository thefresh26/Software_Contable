from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.excel_utils import nuevo_libro, ajustar_columnas, excel_response
from .models import LiquidacionNomina


class ExportarLiquidacionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        mes = request.query_params.get('mes', '')
        año = request.query_params.get('año', '')

        qs = LiquidacionNomina.objects.select_related('empleado').filter(empresa=empresa).order_by('-periodo_fin')
        if mes and año:
            qs = qs.filter(periodo_inicio__year=año, periodo_inicio__month=mes)

        cabeceras = ['Empleado', 'Cédula', 'Período Inicio', 'Período Fin',
                     'Salario Base', 'Total Devengado', 'Total Deducido', 'Neto a Pagar', 'Estado']
        titulo = f'Liquidaciones Nómina {mes}/{año}' if mes and año else 'Liquidaciones Nómina'
        wb, ws, _ = nuevo_libro('Nómina', empresa_nombre, titulo, cabeceras)
        for liq in qs:
            ws.append([
                liq.empleado.nombre, liq.empleado.cedula,
                str(liq.periodo_inicio), str(liq.periodo_fin),
                float(liq.salario_base), float(liq.total_devengado),
                float(liq.total_deducido), float(liq.neto_pagar), liq.estado,
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'liquidaciones_nomina.xlsx')

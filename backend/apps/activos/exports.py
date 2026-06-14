from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.excel_utils import nuevo_libro, ajustar_columnas, excel_response
from .models import ActivoFijo


class ExportarActivosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        qs = ActivoFijo.objects.select_related('categoria').filter(empresa=empresa).order_by('codigo')

        cabeceras = ['Código', 'Nombre', 'Categoría', 'Fecha Compra', 'Valor Compra',
                     'Valor Residual', 'Depreciación Acumulada', 'Valor Neto', 'Estado']
        wb, ws, _ = nuevo_libro('Activos Fijos', empresa_nombre, 'Listado de Activos Fijos', cabeceras)
        estados = dict(ActivoFijo.ESTADOS)
        for a in qs:
            ws.append([
                a.codigo, a.nombre, a.categoria.nombre,
                str(a.fecha_compra), float(a.valor_compra), float(a.valor_residual),
                float(a.depreciacion_acumulada), float(a.valor_neto),
                estados.get(a.estado, a.estado),
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'activos_fijos.xlsx')

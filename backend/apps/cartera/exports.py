from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.excel_utils import nuevo_libro, ajustar_columnas, excel_response
from .models import CuentaPorCobrar, CuentaPorPagar


class ExportarPorCobrarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        qs = CuentaPorCobrar.objects.select_related('factura', 'tercero').filter(empresa=empresa)

        cabeceras = ['Factura', 'Tercero', 'Valor Total', 'Valor Pagado', 'Valor Pendiente', 'Vencimiento', 'Estado']
        wb, ws, _ = nuevo_libro('Cuentas x Cobrar', empresa_nombre, 'Cuentas por Cobrar', cabeceras)
        for c in qs:
            ws.append([
                c.factura.numero, c.tercero.nombre,
                float(c.valor_total), float(c.valor_pagado), float(c.valor_pendiente),
                str(c.fecha_vencimiento), c.estado,
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'por_cobrar.xlsx')


class ExportarPorPagarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        qs = CuentaPorPagar.objects.select_related('factura', 'tercero').filter(empresa=empresa)

        cabeceras = ['Factura', 'Tercero', 'Valor Total', 'Valor Pagado', 'Valor Pendiente', 'Vencimiento', 'Estado']
        wb, ws, _ = nuevo_libro('Cuentas x Pagar', empresa_nombre, 'Cuentas por Pagar', cabeceras)
        for c in qs:
            ws.append([
                c.factura.numero, c.tercero.nombre,
                float(c.valor_total), float(c.valor_pagado), float(c.valor_pendiente),
                str(c.fecha_vencimiento), c.estado,
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'por_pagar.xlsx')

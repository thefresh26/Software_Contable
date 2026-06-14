from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.excel_utils import nuevo_libro, ajustar_columnas, excel_response
from .models import Producto


class ExportarProductosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        qs = Producto.objects.select_related('categoria').filter(empresa=empresa).order_by('nombre')

        cabeceras = ['Código', 'Nombre', 'Categoría', 'Precio Compra', 'Precio Venta', 'IVA %', 'Stock', 'Stock Mínimo', 'Unidad', 'Activo']
        wb, ws, _ = nuevo_libro('Productos', empresa_nombre, 'Inventario de Productos', cabeceras)
        for p in qs:
            ws.append([
                p.codigo, p.nombre,
                p.categoria.nombre if p.categoria else '',
                float(p.precio_compra), float(p.precio_venta),
                float(p.iva_porcentaje), p.stock_actual, p.stock_minimo,
                p.unidad_medida, 'Sí' if p.activo else 'No',
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'productos.xlsx')

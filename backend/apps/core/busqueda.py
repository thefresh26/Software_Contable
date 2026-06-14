from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class BusquedaGlobalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'resultados': [], 'total': 0})

        empresa = getattr(request, 'empresa_activa', None)
        resultados = []

        from apps.terceros.models import Tercero
        for t in Tercero.objects.filter(empresa=empresa, nombre__icontains=q)[:5]:
            resultados.append({
                'tipo': 'Tercero', 'color': 'blue',
                'titulo': t.nombre, 'subtitulo': t.nit,
                'url': '/terceros', 'id': t.id,
            })

        from apps.facturacion.models import Factura
        for f in Factura.objects.filter(empresa=empresa, numero__icontains=q).select_related('tercero')[:5]:
            resultados.append({
                'tipo': 'Factura', 'color': 'green',
                'titulo': f.numero,
                'subtitulo': f'{f.tercero.nombre} — ${f.total:,.0f}',
                'url': '/facturacion', 'id': f.id,
            })

        from apps.inventario.models import Producto
        for p in Producto.objects.filter(empresa=empresa, nombre__icontains=q)[:5]:
            resultados.append({
                'tipo': 'Producto', 'color': 'yellow',
                'titulo': p.nombre,
                'subtitulo': f'Stock: {p.stock_actual} {p.unidad_medida}',
                'url': '/inventario', 'id': p.id,
            })

        from apps.nomina.models import Empleado
        for e in Empleado.objects.filter(empresa=empresa, nombre__icontains=q)[:3]:
            resultados.append({
                'tipo': 'Empleado', 'color': 'purple',
                'titulo': e.nombre, 'subtitulo': e.cargo,
                'url': '/nomina/empleados', 'id': e.id,
            })

        return Response({'resultados': resultados, 'total': len(resultados)})

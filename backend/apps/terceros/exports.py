from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.excel_utils import nuevo_libro, ajustar_columnas, excel_response
from .models import Tercero


class ExportarTercerosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = getattr(request, 'empresa_activa', None)
        empresa_nombre = empresa.nombre if empresa else 'Mi Empresa'
        qs = Tercero.objects.filter(empresa=empresa).order_by('nombre')

        cabeceras = ['Nombre', 'NIT/Cédula', 'Tipo', 'Tipo Persona', 'Email', 'Teléfono', 'Ciudad', 'Activo']
        wb, ws, _ = nuevo_libro('Terceros', empresa_nombre, 'Listado de Terceros', cabeceras)
        tipos = dict(Tercero.TIPOS)
        personas = dict(Tercero.TIPOS_PERSONA)
        for t in qs:
            ws.append([
                t.nombre, t.nit, tipos.get(t.tipo, t.tipo),
                personas.get(t.tipo_persona, t.tipo_persona),
                t.email, t.telefono, t.ciudad,
                'Sí' if t.activo else 'No',
            ])
        ajustar_columnas(ws)
        return excel_response(wb, 'terceros.xlsx')

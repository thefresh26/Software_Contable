from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Empresa, UsuarioEmpresa
from .serializers import EmpresaSerializer, EmpresaConRolSerializer, UsuarioEmpresaSerializer


class EmpresaViewSet(viewsets.ModelViewSet):
    serializer_class = EmpresaSerializer

    def get_queryset(self):
        # Solo empresas a las que pertenece el usuario (o todas si es superusuario)
        if self.request.user.is_superuser:
            return Empresa.objects.all()
        ids = UsuarioEmpresa.objects.filter(
            usuario=self.request.user, activo=True
        ).values_list('empresa_id', flat=True)
        return Empresa.objects.filter(id__in=ids)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return EmpresaConRolSerializer
        return EmpresaSerializer

    def perform_create(self, serializer):
        empresa = serializer.save()
        # El creador queda como administrador de la nueva empresa
        UsuarioEmpresa.objects.create(
            usuario=self.request.user,
            empresa=empresa,
            rol='admin',
        )
        # Si el usuario no tiene empresa activa, la nueva queda activa
        if not self.request.user.empresa_activa:
            self.request.user.empresa_activa = empresa
            self.request.user.save(update_fields=['empresa_activa'])

    @action(detail=True, methods=['post'])
    def cambiar(self, request, pk=None):
        """Cambia la empresa activa del usuario y retorna nuevos tokens JWT."""
        try:
            ue = UsuarioEmpresa.objects.get(
                usuario=request.user,
                empresa_id=pk,
                activo=True,
            )
        except UsuarioEmpresa.DoesNotExist:
            return Response({'error': 'No perteneces a esa empresa.'}, status=status.HTTP_403_FORBIDDEN)

        request.user.empresa_activa = ue.empresa
        request.user.rol = ue.rol
        request.user.save(update_fields=['empresa_activa', 'rol'])

        refresh = RefreshToken.for_user(request.user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'empresa': EmpresaSerializer(ue.empresa).data,
            'rol': ue.rol,
        })

    @action(detail=False, methods=['get'])
    def activa(self, request):
        """Retorna la empresa activa actual del usuario."""
        empresa = request.user.empresa_activa
        if not empresa:
            return Response(None)
        return Response(EmpresaSerializer(empresa).data)

    @action(detail=True, methods=['get', 'post'], url_path='usuarios')
    def usuarios(self, request, pk=None):
        empresa = self.get_object()
        if request.method == 'POST':
            # Agregar usuario existente a la empresa
            usuario_id = request.data.get('usuario_id')
            rol = request.data.get('rol', 'auxiliar')
            from apps.core.models import Usuario
            try:
                usuario = Usuario.objects.get(pk=usuario_id)
            except Usuario.DoesNotExist:
                return Response({'error': 'Usuario no encontrado.'}, status=404)
            ue, created = UsuarioEmpresa.objects.get_or_create(
                usuario=usuario, empresa=empresa,
                defaults={'rol': rol},
            )
            if not created:
                ue.rol = rol
                ue.activo = True
                ue.save(update_fields=['rol', 'activo'])
            return Response(UsuarioEmpresaSerializer(ue).data, status=201)

        ues = UsuarioEmpresa.objects.filter(empresa=empresa).select_related('usuario')
        return Response(UsuarioEmpresaSerializer(ues, many=True).data)

    @action(detail=True, methods=['put', 'delete'], url_path=r'usuarios/(?P<uid>\d+)')
    def usuario_detalle(self, request, pk=None, uid=None):
        empresa = self.get_object()
        try:
            ue = UsuarioEmpresa.objects.get(empresa=empresa, usuario_id=uid)
        except UsuarioEmpresa.DoesNotExist:
            return Response({'error': 'Relación no encontrada.'}, status=404)

        if request.method == 'DELETE':
            ue.activo = False
            ue.save(update_fields=['activo'])
            return Response(status=status.HTTP_204_NO_CONTENT)

        # PUT — cambiar rol
        rol = request.data.get('rol')
        if rol:
            ue.rol = rol
            ue.save(update_fields=['rol'])
        return Response(UsuarioEmpresaSerializer(ue).data)

    @action(detail=True, methods=['post'])
    def invitar(self, request, pk=None):
        """Invita un usuario por email. Si existe, lo agrega directamente."""
        empresa = self.get_object()
        email = request.data.get('email', '').strip()
        rol = request.data.get('rol', 'auxiliar')
        if not email:
            return Response({'error': 'Email requerido.'}, status=400)

        from apps.core.models import Usuario
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({'error': f'No existe un usuario con el email {email}.'}, status=404)

        ue, created = UsuarioEmpresa.objects.get_or_create(
            usuario=usuario, empresa=empresa,
            defaults={'rol': rol},
        )
        if not created:
            ue.rol = rol
            ue.activo = True
            ue.save(update_fields=['rol', 'activo'])
        return Response(UsuarioEmpresaSerializer(ue).data, status=201)

    @action(detail=True, methods=['post'])
    def setup(self, request, pk=None):
        """Carga el PUC estándar colombiano para una empresa nueva."""
        empresa = self.get_object()
        try:
            from apps.contabilidad.models import CuentaPUC
            existentes = CuentaPUC.objects.filter(empresa=empresa).count()
            if existentes > 0:
                return Response({'mensaje': f'La empresa ya tiene {existentes} cuentas PUC.', 'cuentas_creadas': 0})
            # Copiar PUC de empresa por defecto si existe
            cuentas_base = CuentaPUC.objects.filter(empresa__isnull=True) | CuentaPUC.objects.exclude(empresa=empresa)
            cuentas_base = CuentaPUC.objects.filter(empresa__isnull=True).first()
            if cuentas_base is None:
                return Response({'mensaje': 'No hay PUC base disponible. Usa Importar Datos para cargar el PUC.', 'cuentas_creadas': 0})
            # Duplicar todas las cuentas sin empresa para esta empresa
            cuentas = CuentaPUC.objects.filter(empresa__isnull=True)
            creadas = 0
            for c in cuentas:
                CuentaPUC.objects.get_or_create(
                    empresa=empresa,
                    codigo=c.codigo,
                    defaults={
                        'nombre': c.nombre,
                        'tipo': c.tipo,
                        'nivel': c.nivel,
                        'activa': c.activa,
                        'permite_movimiento': c.permite_movimiento,
                    }
                )
                creadas += 1
            return Response({'mensaje': 'Setup completado.', 'cuentas_creadas': creadas})
        except Exception as exc:
            return Response({'error': str(exc)}, status=500)

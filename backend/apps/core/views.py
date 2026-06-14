from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_filters.rest_framework import DjangoFilterBackend
from .models import Usuario, HistorialCambio
from .serializers import UsuarioSerializer, RegistroSerializer
from .mixins import RolRequeridoMixin


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)

    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RegistroView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]


class UsuarioViewSet(RolRequeridoMixin, viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by('username')
    serializer_class = UsuarioSerializer
    roles_permitidos = ['admin']

    @action(detail=True, methods=['patch'], url_path='rol')
    def cambiar_rol(self, request, pk=None):
        usuario = self.get_object()
        nuevo_rol = request.data.get('rol')
        from .models import ROLES
        if nuevo_rol not in dict(ROLES):
            return Response({'error': 'Rol inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        usuario.rol = nuevo_rol
        usuario.save(update_fields=['rol'])
        return Response(UsuarioSerializer(usuario).data)


class HistorialCambioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = None  # defined below
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['modelo', 'accion', 'usuario']

    def get_queryset(self):
        from .models import HistorialCambio
        empresa = getattr(self.request, 'empresa_activa', None)
        qs = HistorialCambio.objects.filter(empresa=empresa).select_related('usuario').order_by('-created_at')
        modelo = self.request.query_params.get('modelo')
        objeto_id = self.request.query_params.get('objeto_id')
        usuario_id = self.request.query_params.get('usuario')
        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')
        if modelo:
            qs = qs.filter(modelo=modelo)
        if objeto_id:
            qs = qs.filter(objeto_id=objeto_id)
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        if desde:
            qs = qs.filter(created_at__date__gte=desde)
        if hasta:
            qs = qs.filter(created_at__date__lte=hasta)
        return qs

    def list(self, request, *args, **kwargs):
        from rest_framework import serializers as drf_serializers

        class HistorialSerializer(drf_serializers.ModelSerializer):
            usuario_nombre = drf_serializers.CharField(source='usuario.username', read_only=True)
            accion_display = drf_serializers.CharField(source='get_accion_display', read_only=True)

            class Meta:
                model = HistorialCambio
                fields = '__all__'

        qs = self.get_queryset()[:200]
        return Response(HistorialSerializer(qs, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ValidarNITView(APIView):
    def get(self, request):
        from apps.terceros.utils import validar_nit, calcular_digito_verificador
        nit = request.query_params.get('nit', '')
        nit_limpio = nit.replace('-', '').replace('.', '').replace(' ', '').strip()
        if not nit_limpio or not nit_limpio.isdigit():
            return Response({'valido': False, 'digito': None, 'mensaje': 'NIT inválido'})
        numero = nit_limpio[:-1] if len(nit_limpio) > 1 else nit_limpio
        digito = calcular_digito_verificador(numero)
        valido = validar_nit(nit)
        return Response({'valido': valido, 'digito': digito, 'nit_limpio': nit_limpio})

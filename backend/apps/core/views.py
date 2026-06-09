from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import Usuario
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

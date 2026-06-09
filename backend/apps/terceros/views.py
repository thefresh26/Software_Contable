from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.empresas.mixins import EmpresaFilterMixin
from .models import Tercero
from .serializers import TerceroSerializer


class TerceroViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Tercero.objects.all()
    serializer_class = TerceroSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo', 'tipo_persona', 'activo']
    search_fields = ['nombre', 'nit', 'email', 'ciudad']
    ordering_fields = ['nombre', 'created_at']
    ordering = ['nombre']

    def create(self, request, *args, **kwargs):
        serializer = TerceroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tercero = serializer.save(empresa=getattr(request, 'empresa_activa', None))
        return Response(TerceroSerializer(tercero).data, status=status.HTTP_201_CREATED)

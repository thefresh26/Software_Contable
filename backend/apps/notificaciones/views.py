from django.core.mail import send_mail
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.empresas.mixins import EmpresaFilterMixin
from .models import Notificacion, ConfiguracionNotificacion
from .serializers import NotificacionSerializer, ConfiguracionNotificacionSerializer
from .services import verificar_alertas


class NotificacionViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['leida', 'tipo', 'prioridad']
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(usuario=self.request.user)

    @action(detail=False, methods=['get'], url_path='no-leidas-count')
    def no_leidas_count(self, request):
        count = self.get_queryset().filter(leida=False).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'], url_path='marcar-leida')
    def marcar_leida(self, request, pk=None):
        notif = self.get_object()
        notif.leida = True
        notif.save(update_fields=['leida'])
        return Response(NotificacionSerializer(notif).data)

    @action(detail=False, methods=['post'], url_path='marcar-todas-leidas')
    def marcar_todas_leidas(self, request):
        actualizadas = self.get_queryset().filter(leida=False).update(leida=True)
        return Response({'actualizadas': actualizadas})

    @action(detail=False, methods=['get', 'put'], url_path='configuracion')
    def configuracion(self, request):
        config, _ = ConfiguracionNotificacion.objects.get_or_create(usuario=request.user)
        if request.method == 'PUT':
            ser = ConfiguracionNotificacionSerializer(config, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data)
        return Response(ConfiguracionNotificacionSerializer(config).data)

    @action(detail=False, methods=['post'], url_path='verificar-alertas')
    def verificar_alertas_manual(self, request):
        if not (request.user.is_superuser or request.user.rol == 'admin'):
            return Response({'error': 'Solo un administrador puede ejecutar esta acción.'}, status=status.HTTP_403_FORBIDDEN)
        verificar_alertas()
        return Response({'mensaje': 'Verificación de alertas ejecutada.'})

    @action(detail=False, methods=['post'], url_path='probar-email')
    def probar_email(self, request):
        usuario = request.user
        if not usuario.email:
            return Response({'error': 'Tu usuario no tiene un correo configurado.'}, status=400)
        send_mail(
            subject='ContaApp — Email de prueba',
            message='Este es un correo de prueba enviado desde tu configuración de notificaciones de ContaApp.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
        return Response({'mensaje': f'Correo de prueba enviado a {usuario.email}.'})

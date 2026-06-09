from rest_framework import serializers
from .models import Notificacion, ConfiguracionNotificacion


class NotificacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)

    class Meta:
        model = Notificacion
        fields = '__all__'
        read_only_fields = ['id', 'usuario', 'created_at', 'email_enviado']


class ConfiguracionNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionNotificacion
        fields = '__all__'
        read_only_fields = ['id', 'usuario']

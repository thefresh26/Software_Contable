from django.contrib import admin
from .models import Notificacion, ConfiguracionNotificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'usuario', 'tipo', 'prioridad', 'leida', 'email_enviado', 'created_at']
    list_filter = ['tipo', 'prioridad', 'leida', 'email_enviado']
    search_fields = ['titulo', 'mensaje', 'usuario__username']


@admin.register(ConfiguracionNotificacion)
class ConfiguracionNotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'dias_anticipacion_factura', 'dias_anticipacion_cotizacion']
    search_fields = ['usuario__username']

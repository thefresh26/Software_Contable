from django.db import models


class Notificacion(models.Model):
    TIPOS = [
        ('factura_vencer', 'Factura por Vencer'),
        ('factura_vencida', 'Factura Vencida'),
        ('stock_bajo', 'Stock Bajo'),
        ('pago_recibido', 'Pago Recibido'),
        ('pago_realizado', 'Pago Realizado'),
        ('nomina_pendiente', 'Nómina Pendiente'),
        ('activo_depreciado', 'Activo Totalmente Depreciado'),
        ('cotizacion_vencer', 'Cotización por Vencer'),
        ('sistema', 'Notificación del Sistema'),
    ]
    PRIORIDADES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='notificaciones',
    )
    usuario = models.ForeignKey('core.Usuario', on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=30, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='media')
    leida = models.BooleanField(default=False)
    email_enviado = models.BooleanField(default=False)
    url_accion = models.CharField(max_length=200, blank=True)
    objeto_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.titulo} — {self.usuario}'


class ConfiguracionNotificacion(models.Model):
    usuario = models.OneToOneField('core.Usuario', on_delete=models.CASCADE, related_name='config_notificaciones')

    email_facturas_vencer = models.BooleanField(default=True)
    email_facturas_vencidas = models.BooleanField(default=True)
    email_stock_bajo = models.BooleanField(default=True)
    email_pagos = models.BooleanField(default=True)
    email_nomina = models.BooleanField(default=True)
    email_cotizaciones = models.BooleanField(default=True)

    dias_anticipacion_factura = models.IntegerField(default=5)
    dias_anticipacion_cotizacion = models.IntegerField(default=3)

    sistema_stock_bajo = models.BooleanField(default=True)
    sistema_facturas_vencer = models.BooleanField(default=True)
    sistema_pagos = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Configuración de Notificaciones'
        verbose_name_plural = 'Configuraciones de Notificaciones'

    def __str__(self):
        return f'Configuración de {self.usuario}'

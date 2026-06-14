from django.contrib.auth.models import AbstractUser
from django.db import models

ROLES = [
    ('admin', 'Administrador'),
    ('contador', 'Contador'),
    ('auxiliar', 'Auxiliar Contable'),
    ('gerente', 'Gerente'),
    ('vendedor', 'Vendedor'),
]


class Usuario(AbstractUser):
    empresa = models.CharField(max_length=200, blank=True)
    nit_empresa = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='auxiliar')
    empresa_activa = models.ForeignKey(
        'empresas.Empresa',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='usuarios_activos',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        nombre_empresa = self.empresa_activa.nombre if self.empresa_activa else (self.empresa or '')
        return f"{self.get_full_name() or self.username} — {nombre_empresa}"


class HistorialCambio(models.Model):
    ACCIONES = [
        ('crear', 'Creación'),
        ('editar', 'Edición'),
        ('eliminar', 'Eliminación'),
        ('emitir', 'Emisión'),
        ('anular', 'Anulación'),
    ]
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='historial_cambios',
    )
    usuario = models.ForeignKey(
        'core.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='historial_cambios',
    )
    accion = models.CharField(max_length=20, choices=ACCIONES)
    modelo = models.CharField(max_length=50)
    objeto_id = models.IntegerField()
    objeto_repr = models.CharField(max_length=200)
    cambios = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de Cambio'
        verbose_name_plural = 'Historial de Cambios'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.accion} {self.modelo} #{self.objeto_id} por {self.usuario}"

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

from django.db import models

ROLES_EMPRESA = [
    ('admin', 'Administrador'),
    ('contador', 'Contador'),
    ('auxiliar', 'Auxiliar Contable'),
    ('gerente', 'Gerente'),
    ('vendedor', 'Vendedor'),
]


class Empresa(models.Model):
    nombre = models.CharField(max_length=200)
    nit = models.CharField(max_length=20, unique=True)
    razon_social = models.CharField(max_length=200)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    representante_legal = models.CharField(max_length=200, blank=True)
    regimen = models.CharField(
        max_length=20,
        choices=[('comun', 'Régimen Común'), ('simplificado', 'Régimen Simplificado')],
        default='comun',
    )
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.nit})"


class UsuarioEmpresa(models.Model):
    """Relación usuario-empresa con rol específico por empresa."""

    usuario = models.ForeignKey('core.Usuario', on_delete=models.CASCADE, related_name='usuario_empresas')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios')
    rol = models.CharField(max_length=20, choices=ROLES_EMPRESA, default='auxiliar')
    activo = models.BooleanField(default=True)
    fecha_ingreso = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario de Empresa'
        verbose_name_plural = 'Usuarios de Empresa'
        unique_together = ('usuario', 'empresa')

    def __str__(self):
        return f"{self.usuario} — {self.empresa} ({self.rol})"

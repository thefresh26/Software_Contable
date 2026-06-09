from django.db import models


class Tercero(models.Model):
    TIPOS = [
        ('cliente', 'Cliente'),
        ('proveedor', 'Proveedor'),
        ('ambos', 'Ambos'),
    ]
    TIPOS_PERSONA = [
        ('natural', 'Persona Natural'),
        ('juridica', 'Persona Jurídica'),
    ]

    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='terceros',
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    tipo_persona = models.CharField(max_length=20, choices=TIPOS_PERSONA, default='natural')
    nombre = models.CharField(max_length=200)
    nit = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tercero'
        verbose_name_plural = 'Terceros'
        ordering = ['nombre']
        unique_together = [('empresa', 'nit')]

    def __str__(self):
        return f"{self.nombre} ({self.nit})"

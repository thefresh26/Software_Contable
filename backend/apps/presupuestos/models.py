from django.db import models
from django.db.models import Max
import datetime


def _siguiente_numero_cot(empresa=None):
    año = datetime.date.today().year
    prefijo = f"COT-{año}-"
    qs = Cotizacion.objects.filter(numero__startswith=prefijo)
    if empresa is not None:
        qs = qs.filter(empresa=empresa)
    ultimo = qs.aggregate(Max('numero'))['numero__max']
    seq = (int(ultimo.split('-')[-1]) + 1) if ultimo else 1
    return f"{prefijo}{seq:04d}"


class Cotizacion(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='cotizaciones',
    )
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('vencida', 'Vencida'),
    ]

    numero = models.CharField(max_length=20, blank=True)
    tercero = models.ForeignKey('terceros.Tercero', on_delete=models.PROTECT, related_name='cotizaciones')
    fecha = models.DateField()
    fecha_vencimiento = models.DateField()
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    observaciones = models.TextField(blank=True)
    terminos = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha', '-created_at']
        unique_together = [('empresa', 'numero')]

    def __str__(self):
        return f"{self.numero} — {self.tercero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = _siguiente_numero_cot(empresa=self.empresa_id)
        super().save(*args, **kwargs)

    def recalcular_totales(self):
        detalles = self.detalles.all()
        self.subtotal = sum(d.subtotal for d in detalles)
        self.iva = sum(d.iva_valor for d in detalles)
        self.total = sum(d.total for d in detalles)
        self.save(update_fields=['subtotal', 'iva', 'total'])


class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('inventario.Producto', null=True, blank=True, on_delete=models.SET_NULL)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=19)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva_valor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_unitario * self.cantidad
        self.iva_valor = self.subtotal * self.iva_porcentaje / 100
        self.total = self.subtotal + self.iva_valor
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.descripcion} x{self.cantidad}"


class Presupuesto(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='presupuestos',
    )
    ESTADOS = [
        ('activo', 'Activo'),
        ('cerrado', 'Cerrado'),
    ]

    nombre = models.CharField(max_length=200)
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        ordering = ['-periodo_inicio']

    def __str__(self):
        return f"{self.nombre} ({self.periodo_inicio} — {self.periodo_fin})"


class ItemPresupuesto(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='items')
    cuenta = models.ForeignKey('contabilidad.CuentaPUC', on_delete=models.PROTECT)
    descripcion = models.CharField(max_length=200)
    valor_presupuestado = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.cuenta} — {self.valor_presupuestado}"

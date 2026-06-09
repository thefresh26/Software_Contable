from django.db import models
from django.db.models import Max
import datetime


def _siguiente_numero(tipo, empresa=None):
    año = datetime.date.today().year
    prefijo = f"{tipo}-{año}-"
    qs = Factura.objects.filter(numero__startswith=prefijo)
    if empresa is not None:
        qs = qs.filter(empresa=empresa)
    ultimo = qs.aggregate(Max('numero'))['numero__max']
    if ultimo:
        seq = int(ultimo.split('-')[-1]) + 1
    else:
        seq = 1
    return f"{prefijo}{seq:04d}"


class TipoRetencion(models.Model):
    TIPOS = [
        ('reteiva', 'ReteIVA'),
        ('reteica', 'ReteICA'),
        ('retefuente', 'ReteFuente'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPOS)
    nombre = models.CharField(max_length=200)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    cuenta_contable = models.ForeignKey(
        'contabilidad.CuentaPUC', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tipos_retencion'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Retención'
        verbose_name_plural = 'Tipos de Retención'
        ordering = ['tipo', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"


class Factura(models.Model):
    TIPOS = [
        ('FV', 'Factura de Venta'),
        ('FC', 'Factura de Compra'),
        ('NC', 'Nota Crédito'),
        ('ND', 'Nota Débito'),
    ]
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida'),
        ('anulada', 'Anulada'),
    ]

    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='facturas',
    )
    numero = models.CharField(max_length=20, blank=True)
    tipo = models.CharField(max_length=2, choices=TIPOS)
    tercero = models.ForeignKey('terceros.Tercero', on_delete=models.PROTECT, related_name='facturas')
    fecha = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha', '-created_at']
        unique_together = [('empresa', 'numero')]

    def __str__(self):
        return f"{self.numero} — {self.tercero}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = _siguiente_numero(self.tipo, empresa=self.empresa_id)
        super().save(*args, **kwargs)

    def recalcular_totales(self):
        detalles = self.detalles.all()
        self.subtotal = sum(d.subtotal for d in detalles)
        self.iva = sum(d.iva_valor for d in detalles)
        self.descuento = sum(d.precio_unitario * d.cantidad * d.descuento_porcentaje / 100
                             for d in detalles)
        self.total = sum(d.total for d in detalles)
        self.save(update_fields=['subtotal', 'iva', 'descuento', 'total'])

    @property
    def total_retenciones(self):
        return sum(r.valor for r in self.retenciones.all())

    @property
    def neto_pagar(self):
        return self.total - self.total_retenciones


class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('inventario.Producto', null=True, blank=True, on_delete=models.SET_NULL)
    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=19)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva_valor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Detalle de Factura'
        verbose_name_plural = 'Detalles de Factura'

    def save(self, *args, **kwargs):
        base = self.precio_unitario * self.cantidad
        descuento_val = base * self.descuento_porcentaje / 100
        self.subtotal = base - descuento_val
        self.iva_valor = self.subtotal * self.iva_porcentaje / 100
        self.total = self.subtotal + self.iva_valor
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"


class RetencionFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='retenciones')
    tipo_retencion = models.ForeignKey(TipoRetencion, on_delete=models.PROTECT)
    base = models.DecimalField(max_digits=15, decimal_places=2)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    valor = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        verbose_name = 'Retención de Factura'
        verbose_name_plural = 'Retenciones de Factura'

    def __str__(self):
        return f"{self.tipo_retencion} — {self.valor}"

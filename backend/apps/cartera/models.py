from decimal import Decimal
from django.db import models, transaction

MEDIOS_PAGO = [
    ('efectivo', 'Efectivo'),
    ('transferencia', 'Transferencia'),
    ('cheque', 'Cheque'),
]

ESTADOS_CARTERA = [
    ('pendiente', 'Pendiente'),
    ('parcial', 'Pago Parcial'),
    ('pagada', 'Pagada'),
    ('vencida', 'Vencida'),
]


class CuentaPorCobrar(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='cuentas_cobrar',
    )
    factura = models.OneToOneField(
        'facturacion.Factura', on_delete=models.PROTECT, related_name='cuenta_cobrar'
    )
    tercero = models.ForeignKey(
        'terceros.Tercero', on_delete=models.PROTECT, related_name='cuentas_cobrar'
    )
    valor_total = models.DecimalField(max_digits=15, decimal_places=2)
    valor_pagado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_pendiente = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS_CARTERA, default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cuenta por Cobrar'
        verbose_name_plural = 'Cuentas por Cobrar'
        ordering = ['fecha_vencimiento']

    def __str__(self):
        return f"CxC {self.factura.numero} — {self.tercero} — {self.valor_pendiente}"

    def actualizar_estado(self):
        import datetime
        if self.valor_pagado >= self.valor_total:
            self.estado = 'pagada'
        elif self.valor_pagado > 0:
            self.estado = 'parcial'
        elif self.fecha_vencimiento < datetime.date.today():
            self.estado = 'vencida'
        else:
            self.estado = 'pendiente'
        self.valor_pendiente = self.valor_total - self.valor_pagado
        self.save(update_fields=['estado', 'valor_pagado', 'valor_pendiente'])


class CuentaPorPagar(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='cuentas_pagar',
    )
    factura = models.OneToOneField(
        'facturacion.Factura', on_delete=models.PROTECT, related_name='cuenta_pagar'
    )
    tercero = models.ForeignKey(
        'terceros.Tercero', on_delete=models.PROTECT, related_name='cuentas_pagar'
    )
    valor_total = models.DecimalField(max_digits=15, decimal_places=2)
    valor_pagado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_pendiente = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS_CARTERA, default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cuenta por Pagar'
        verbose_name_plural = 'Cuentas por Pagar'
        ordering = ['fecha_vencimiento']

    def __str__(self):
        return f"CxP {self.factura.numero} — {self.tercero} — {self.valor_pendiente}"

    def actualizar_estado(self):
        import datetime
        if self.valor_pagado >= self.valor_total:
            self.estado = 'pagada'
        elif self.valor_pagado > 0:
            self.estado = 'parcial'
        elif self.fecha_vencimiento < datetime.date.today():
            self.estado = 'vencida'
        else:
            self.estado = 'pendiente'
        self.valor_pendiente = self.valor_total - self.valor_pagado
        self.save(update_fields=['estado', 'valor_pagado', 'valor_pendiente'])


class DescuentoProntoPago(models.Model):
    cuenta_cobrar = models.ForeignKey(
        'CuentaPorCobrar', on_delete=models.CASCADE, related_name='descuentos'
    )
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    dias_plazo = models.IntegerField()
    fecha_limite = models.DateField()
    valor_descuento = models.DecimalField(max_digits=15, decimal_places=2)
    aplicado = models.BooleanField(default=False)
    fecha_aplicacion = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Descuento por Pronto Pago'
        verbose_name_plural = 'Descuentos por Pronto Pago'
        ordering = ['fecha_limite']

    def __str__(self):
        return f"Dto {self.porcentaje}% CxC#{self.cuenta_cobrar_id} — hasta {self.fecha_limite}"


def _recalcular_cxc(cuenta_cobrar_id):
    """Recalcula valor_pagado de CxC desde la DB (evita cache de FK)."""
    from django.db.models import Sum
    cxc = CuentaPorCobrar.objects.select_for_update().get(pk=cuenta_cobrar_id)
    total = PagoRecibido.objects.filter(cuenta_cobrar_id=cuenta_cobrar_id).aggregate(s=Sum('valor'))['s'] or 0
    cxc.valor_pagado = total
    cxc.actualizar_estado()


class PagoRecibido(models.Model):
    cuenta_cobrar = models.ForeignKey(CuentaPorCobrar, on_delete=models.PROTECT, related_name='pagos')
    fecha = models.DateField()
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    medio_pago = models.CharField(max_length=20, choices=MEDIOS_PAGO)
    referencia = models.CharField(max_length=100, blank=True)
    observacion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago Recibido'
        verbose_name_plural = 'Pagos Recibidos'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            _recalcular_cxc(self.cuenta_cobrar_id)


class PagoRealizado(models.Model):
    cuenta_pagar = models.ForeignKey(CuentaPorPagar, on_delete=models.PROTECT, related_name='pagos')
    fecha = models.DateField()
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    medio_pago = models.CharField(max_length=20, choices=MEDIOS_PAGO)
    referencia = models.CharField(max_length=100, blank=True)
    observacion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago Realizado'
        verbose_name_plural = 'Pagos Realizados'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            from django.db.models import Sum
            cxp = CuentaPorPagar.objects.select_for_update().get(pk=self.cuenta_pagar_id)
            total = PagoRealizado.objects.filter(cuenta_pagar_id=self.cuenta_pagar_id).aggregate(s=Sum('valor'))['s'] or 0
            cxp.valor_pagado = total
            cxp.actualizar_estado()

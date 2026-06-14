import datetime
from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError


class CentroCosto(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='centros_costo',
    )
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    padre = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='hijos'
    )

    class Meta:
        verbose_name = 'Centro de Costo'
        verbose_name_plural = 'Centros de Costo'
        ordering = ['codigo']
        unique_together = [('empresa', 'codigo')]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class CuentaPUC(models.Model):
    TIPOS = [
        ('activo', 'Activo'),
        ('pasivo', 'Pasivo'),
        ('patrimonio', 'Patrimonio'),
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto'),
        ('costo', 'Costo'),
    ]

    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='cuentas_puc',
    )
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    padre = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='hijos'
    )
    nivel = models.IntegerField()
    activa = models.BooleanField(default=True)
    permite_movimiento = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cuenta PUC'
        verbose_name_plural = 'Cuentas PUC'
        ordering = ['codigo']
        unique_together = [('empresa', 'codigo')]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"

    @property
    def saldo(self):
        movs = self.movimientos.aggregate(
            total_debito=Sum('debito'),
            total_credito=Sum('credito'),
        )
        debito = movs['total_debito'] or 0
        credito = movs['total_credito'] or 0
        if self.tipo in ('activo', 'gasto', 'costo'):
            return debito - credito
        return credito - debito


class CierrePeriodo(models.Model):
    ESTADOS = [('abierto', 'Abierto'), ('cerrado', 'Cerrado')]

    empresa = models.ForeignKey(
        'empresas.Empresa', on_delete=models.CASCADE, related_name='cierres_periodo',
    )
    periodo = models.DateField()  # primer día del mes: 2024-01-01
    estado = models.CharField(max_length=20, choices=ESTADOS, default='abierto')
    cerrado_por = models.ForeignKey(
        'core.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='cierres_realizados'
    )
    cerrado_at = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Cierre de Período'
        verbose_name_plural = 'Cierres de Período'
        ordering = ['-periodo']
        unique_together = [('empresa', 'periodo')]

    def __str__(self):
        return f"Cierre {self.periodo.strftime('%Y-%m')} — {self.get_estado_display()}"

    def periodo_fin(self):
        import calendar
        last_day = calendar.monthrange(self.periodo.year, self.periodo.month)[1]
        return datetime.date(self.periodo.year, self.periodo.month, last_day)


class AsientoContable(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='asientos',
    )
    fecha = models.DateField()
    descripcion = models.TextField()
    factura = models.OneToOneField(
        'facturacion.Factura', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='asiento'
    )
    nomina = models.OneToOneField(
        'nomina.LiquidacionNomina', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='asiento'
    )
    es_manual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Asiento Contable'
        verbose_name_plural = 'Asientos Contables'
        ordering = ['-fecha', '-created_at']

    def __str__(self):
        return f"Asiento {self.pk} — {self.fecha} — {self.descripcion[:50]}"

    def save(self, *args, **kwargs):
        if self.fecha and self.empresa_id:
            primer_dia = datetime.date(self.fecha.year, self.fecha.month, 1)
            if CierrePeriodo.objects.filter(
                empresa_id=self.empresa_id,
                periodo=primer_dia,
                estado='cerrado',
            ).exists():
                raise ValidationError(
                    f"El período {primer_dia.strftime('%B %Y')} está cerrado. "
                    "No se pueden crear ni modificar asientos."
                )
        super().save(*args, **kwargs)

    def esta_cuadrado(self):
        totales = self.movimientos.aggregate(
            total_debito=Sum('debito'),
            total_credito=Sum('credito'),
        )
        return (totales['total_debito'] or 0) == (totales['total_credito'] or 0)


class MovimientoContable(models.Model):
    asiento = models.ForeignKey(
        AsientoContable, on_delete=models.CASCADE, related_name='movimientos'
    )
    cuenta = models.ForeignKey(
        CuentaPUC, on_delete=models.PROTECT, related_name='movimientos'
    )
    centro_costo = models.ForeignKey(
        CentroCosto, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='movimientos'
    )
    descripcion = models.CharField(max_length=200, blank=True)
    debito = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credito = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Movimiento Contable'
        verbose_name_plural = 'Movimientos Contables'

    def __str__(self):
        return f"{self.cuenta.codigo} D:{self.debito} C:{self.credito}"

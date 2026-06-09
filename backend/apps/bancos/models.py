from django.db import models


class CuentaBancaria(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='cuentas_bancarias',
    )
    TIPOS = [
        ('corriente', 'Cuenta Corriente'),
        ('ahorros', 'Cuenta de Ahorros'),
        ('fiduciaria', 'Cuenta Fiduciaria'),
    ]

    nombre = models.CharField(max_length=200)
    banco = models.CharField(max_length=100)
    numero_cuenta = models.CharField(max_length=30, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    cuenta_contable = models.ForeignKey(
        'contabilidad.CuentaPUC', on_delete=models.PROTECT, related_name='cuentas_bancarias'
    )
    saldo_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} — {self.numero_cuenta}"


class ExtractoBancario(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='extractos_bancarios',
    )
    ESTADOS = [
        ('pendiente', 'Pendiente de Conciliar'),
        ('conciliado', 'Conciliado'),
        ('parcial', 'Parcialmente Conciliado'),
    ]

    cuenta = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, related_name='extractos')
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    saldo_inicial_extracto = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_final_extracto = models.DecimalField(max_digits=15, decimal_places=2)
    total_debitos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_creditos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    archivo_original = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Extracto Bancario'
        verbose_name_plural = 'Extractos Bancarios'
        ordering = ['-periodo_fin']

    def __str__(self):
        return f"{self.cuenta} — {self.periodo_inicio} a {self.periodo_fin}"


class MovimientoBancario(models.Model):
    """Línea del extracto bancario"""
    TIPOS = [
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
    ]

    extracto = models.ForeignKey(ExtractoBancario, on_delete=models.CASCADE, related_name='movimientos')
    fecha = models.DateField()
    descripcion = models.CharField(max_length=300)
    referencia = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    conciliado = models.BooleanField(default=False)
    asiento_contable = models.ForeignKey(
        'contabilidad.AsientoContable',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='movimientos_bancarios'
    )

    class Meta:
        verbose_name = 'Movimiento Bancario'
        verbose_name_plural = 'Movimientos Bancarios'
        ordering = ['fecha']

    def __str__(self):
        return f"{self.fecha} — {self.descripcion[:40]} — {self.valor}"


class ConciliacionBancaria(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='conciliaciones_bancarias',
    )
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('finalizada', 'Finalizada'),
    ]

    cuenta = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, related_name='conciliaciones')
    extracto = models.ForeignKey(ExtractoBancario, on_delete=models.PROTECT, related_name='conciliaciones')
    periodo = models.DateField()  # mes de la conciliación
    saldo_extracto = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_libros = models.DecimalField(max_digits=15, decimal_places=2)
    diferencia = models.DecimalField(max_digits=15, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finalizada_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Conciliación Bancaria'
        verbose_name_plural = 'Conciliaciones Bancarias'
        ordering = ['-periodo']

    def __str__(self):
        return f"Conciliación {self.cuenta} — {self.periodo}"


class PartidaConciliacion(models.Model):
    """Partidas en tránsito o diferencias identificadas"""
    TIPOS = [
        ('cheque_girado', 'Cheque Girado No Cobrado'),
        ('deposito_transito', 'Depósito en Tránsito'),
        ('nota_debito', 'Nota Débito Banco No Registrada'),
        ('nota_credito', 'Nota Crédito Banco No Registrada'),
        ('error_libros', 'Error en Libros'),
        ('error_banco', 'Error del Banco'),
        ('otro', 'Otro'),
    ]
    AFECTA = [
        ('extracto', 'Extracto'),
        ('libros', 'Libros'),
    ]

    conciliacion = models.ForeignKey(ConciliacionBancaria, on_delete=models.CASCADE, related_name='partidas')
    tipo = models.CharField(max_length=30, choices=TIPOS)
    descripcion = models.CharField(max_length=300)
    fecha = models.DateField()
    valor = models.DecimalField(
        max_digits=15, decimal_places=2,
        help_text='Con signo: positivo aumenta el saldo del lado que afecta, negativo lo disminuye'
    )
    afecta = models.CharField(max_length=10, choices=AFECTA)
    resuelta = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Partida de Conciliación'
        verbose_name_plural = 'Partidas de Conciliación'
        ordering = ['fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.descripcion[:40]}"

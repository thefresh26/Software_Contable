from django.db import models


METODOS_DEPRECIACION = [
    ('linea_recta', 'Línea Recta'),
    ('reduccion_saldos', 'Reducción de Saldos'),
    ('suma_digitos', 'Suma de Dígitos de los Años'),
]


class CategoriaActivo(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='categorias_activos',
    )
    nombre = models.CharField(max_length=100)
    vida_util_años = models.IntegerField()
    metodo_depreciacion = models.CharField(max_length=20, choices=METODOS_DEPRECIACION, default='linea_recta')
    cuenta_activo = models.ForeignKey(
        'contabilidad.CuentaPUC', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='cat_activo',
    )
    cuenta_depreciacion = models.ForeignKey(
        'contabilidad.CuentaPUC', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='cat_depreciacion',
    )
    cuenta_gasto_depreciacion = models.ForeignKey(
        'contabilidad.CuentaPUC', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='cat_gasto_dep',
    )

    class Meta:
        verbose_name = 'Categoría de Activo'
        verbose_name_plural = 'Categorías de Activos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ActivoFijo(models.Model):
    ESTADOS = [
        ('activo', 'Activo'),
        ('depreciado', 'Totalmente Depreciado'),
        ('dado_baja', 'Dado de Baja'),
        ('vendido', 'Vendido'),
    ]

    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='activos_fijos',
    )
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(CategoriaActivo, on_delete=models.PROTECT, related_name='activos')
    fecha_compra = models.DateField()
    fecha_inicio_depreciacion = models.DateField()
    valor_compra = models.DecimalField(max_digits=15, decimal_places=2)
    valor_residual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vida_util_años = models.IntegerField()
    metodo_depreciacion = models.CharField(max_length=20, choices=METODOS_DEPRECIACION, default='linea_recta')
    valor_depreciado_acumulado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_en_libros = models.DecimalField(max_digits=15, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    ubicacion = models.CharField(max_length=200, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    proveedor = models.ForeignKey('terceros.Tercero', null=True, blank=True, on_delete=models.SET_NULL, related_name='activos_vendidos')
    factura_compra = models.ForeignKey('facturacion.Factura', null=True, blank=True, on_delete=models.SET_NULL, related_name='activos_comprados')
    cuenta_activo = models.ForeignKey(
        'contabilidad.CuentaPUC', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='activos',
    )
    cuenta_depreciacion_acumulada = models.ForeignKey(
        'contabilidad.CuentaPUC', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='dep_acumulada',
    )
    cuenta_gasto_depreciacion = models.ForeignKey(
        'contabilidad.CuentaPUC', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='gasto_dep',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Activo Fijo'
        verbose_name_plural = 'Activos Fijos'
        ordering = ['codigo']
        unique_together = [('empresa', 'codigo')]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"

    @property
    def porcentaje_depreciado(self):
        base = self.valor_compra - self.valor_residual
        if base <= 0:
            return 0
        return float(min(self.valor_depreciado_acumulado / base * 100, 100))

    def save(self, *args, **kwargs):
        self.valor_en_libros = self.valor_compra - self.valor_depreciado_acumulado
        super().save(*args, **kwargs)


class DepreciacionMensual(models.Model):
    activo = models.ForeignKey(ActivoFijo, on_delete=models.CASCADE, related_name='depreciaciones')
    periodo = models.DateField()
    valor_depreciacion = models.DecimalField(max_digits=15, decimal_places=2)
    valor_acumulado = models.DecimalField(max_digits=15, decimal_places=2)
    valor_en_libros = models.DecimalField(max_digits=15, decimal_places=2)
    asiento = models.ForeignKey('contabilidad.AsientoContable', null=True, blank=True, on_delete=models.SET_NULL, related_name='depreciaciones')
    aplicada = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Depreciación Mensual'
        verbose_name_plural = 'Depreciaciones Mensuales'
        ordering = ['-periodo']
        unique_together = ['activo', 'periodo']

    def __str__(self):
        return f"{self.activo.codigo} — {self.periodo.strftime('%Y-%m')}"


class BajaActivo(models.Model):
    activo = models.OneToOneField(ActivoFijo, on_delete=models.CASCADE, related_name='baja')
    fecha = models.DateField()
    motivo = models.CharField(max_length=200)
    valor_venta = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    utilidad_perdida = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    asiento = models.ForeignKey('contabilidad.AsientoContable', null=True, blank=True, on_delete=models.SET_NULL, related_name='bajas_activos')
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Baja de Activo'
        verbose_name_plural = 'Bajas de Activos'
        ordering = ['-fecha']

    def __str__(self):
        return f"Baja {self.activo.codigo} — {self.fecha}"

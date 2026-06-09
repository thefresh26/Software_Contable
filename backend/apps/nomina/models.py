from decimal import Decimal
from django.db import models


SMMLV_2024 = Decimal('1_300_000')
AUXILIO_TRANSPORTE_2024 = Decimal('162_000')


class Empleado(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='empleados',
    )
    TIPOS_CONTRATO = [
        ('indefinido', 'Indefinido'),
        ('fijo', 'Término fijo'),
        ('obra_labor', 'Obra o labor'),
    ]

    nombre = models.CharField(max_length=200)
    cedula = models.CharField(max_length=20)
    cargo = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100, blank=True)
    salario_base = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_ingreso = models.DateField()
    tipo_contrato = models.CharField(max_length=20, choices=TIPOS_CONTRATO, default='indefinido')
    activo = models.BooleanField(default=True)
    cuenta_bancaria = models.CharField(max_length=30, blank=True)
    banco = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['nombre']
        unique_together = [('empresa', 'cedula')]

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"


class LiquidacionNomina(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa', null=True, blank=True,
        on_delete=models.CASCADE, related_name='liquidaciones_nomina',
    )
    ESTADOS = [
        ('liquidada', 'Liquidada'),
        ('pagada', 'Pagada'),
    ]

    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='liquidaciones')
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()

    # Devengados
    salario_base = models.DecimalField(max_digits=15, decimal_places=2)
    auxilio_transporte = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    horas_extra_diurnas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_horas_extra_diurnas = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    horas_extra_nocturnas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_horas_extra_nocturnas = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bonificaciones = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_devengado = models.DecimalField(max_digits=15, decimal_places=2)

    # Deducciones empleado
    salud_empleado = models.DecimalField(max_digits=15, decimal_places=2)    # 4%
    pension_empleado = models.DecimalField(max_digits=15, decimal_places=2)  # 4%
    retencion_fuente = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    otras_deducciones = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deducido = models.DecimalField(max_digits=15, decimal_places=2)

    # Aportes empresa
    salud_empresa = models.DecimalField(max_digits=15, decimal_places=2)      # 8.5%
    pension_empresa = models.DecimalField(max_digits=15, decimal_places=2)    # 12%
    arl = models.DecimalField(max_digits=15, decimal_places=2)                # 0.522% riesgo I
    caja_compensacion = models.DecimalField(max_digits=15, decimal_places=2)  # 4%
    sena = models.DecimalField(max_digits=15, decimal_places=2)               # 2%
    icbf = models.DecimalField(max_digits=15, decimal_places=2)               # 3%

    neto_pagar = models.DecimalField(max_digits=15, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='liquidada')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Liquidación de Nómina'
        verbose_name_plural = 'Liquidaciones de Nómina'
        ordering = ['-periodo_fin']
        unique_together = ('empleado', 'periodo_inicio', 'periodo_fin')

    def __str__(self):
        return f"{self.empleado} — {self.periodo_inicio} a {self.periodo_fin}"


def calcular_nomina(empleado, periodo_inicio, periodo_fin,
                    bonificaciones=Decimal('0'),
                    horas_extra_diurnas=Decimal('0'),
                    horas_extra_nocturnas=Decimal('0'),
                    retencion_fuente=Decimal('0'),
                    otras_deducciones=Decimal('0')):
    dias = (periodo_fin - periodo_inicio).days + 1
    salario_proporcional = (empleado.salario_base * dias / 30).quantize(Decimal('0.01'))

    aux_transporte = (
        AUXILIO_TRANSPORTE_2024
        if empleado.salario_base <= 2 * SMMLV_2024
        else Decimal('0')
    )

    # Horas extra diurnas: recargo 25% sobre valor hora ordinaria
    valor_hora = empleado.salario_base / 240
    val_he_diurnas = (valor_hora * Decimal('1.25') * horas_extra_diurnas).quantize(Decimal('0.01'))
    # Horas extra nocturnas: recargo 75%
    val_he_nocturnas = (valor_hora * Decimal('1.75') * horas_extra_nocturnas).quantize(Decimal('0.01'))

    total_devengado = (
        salario_proporcional + aux_transporte + bonificaciones
        + val_he_diurnas + val_he_nocturnas
    ).quantize(Decimal('0.01'))

    salud_emp = (total_devengado * Decimal('0.04')).quantize(Decimal('0.01'))
    pension_emp = (total_devengado * Decimal('0.04')).quantize(Decimal('0.01'))
    total_deducido = (salud_emp + pension_emp + retencion_fuente + otras_deducciones).quantize(Decimal('0.01'))

    salud_empresa = (total_devengado * Decimal('0.085')).quantize(Decimal('0.01'))
    pension_empresa = (total_devengado * Decimal('0.12')).quantize(Decimal('0.01'))
    arl = (total_devengado * Decimal('0.00522')).quantize(Decimal('0.01'))
    caja = (total_devengado * Decimal('0.04')).quantize(Decimal('0.01'))
    sena = (total_devengado * Decimal('0.02')).quantize(Decimal('0.01'))
    icbf = (total_devengado * Decimal('0.03')).quantize(Decimal('0.01'))

    neto = (total_devengado - total_deducido).quantize(Decimal('0.01'))

    return {
        'salario_base': salario_proporcional,
        'auxilio_transporte': aux_transporte,
        'horas_extra_diurnas': horas_extra_diurnas,
        'valor_horas_extra_diurnas': val_he_diurnas,
        'horas_extra_nocturnas': horas_extra_nocturnas,
        'valor_horas_extra_nocturnas': val_he_nocturnas,
        'bonificaciones': bonificaciones,
        'total_devengado': total_devengado,
        'salud_empleado': salud_emp,
        'pension_empleado': pension_emp,
        'retencion_fuente': retencion_fuente,
        'otras_deducciones': otras_deducciones,
        'total_deducido': total_deducido,
        'salud_empresa': salud_empresa,
        'pension_empresa': pension_empresa,
        'arl': arl,
        'caja_compensacion': caja,
        'sena': sena,
        'icbf': icbf,
        'neto_pagar': neto,
    }

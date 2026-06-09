from django.contrib import admin
from .models import Empleado, LiquidacionNomina


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cedula', 'cargo', 'departamento', 'salario_base', 'activo']
    list_filter = ['activo', 'tipo_contrato', 'departamento']
    search_fields = ['nombre', 'cedula']


@admin.register(LiquidacionNomina)
class LiquidacionNominaAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'periodo_inicio', 'periodo_fin', 'total_devengado',
                    'total_deducido', 'neto_pagar', 'estado']
    list_filter = ['estado', 'periodo_inicio']
    readonly_fields = [
        'salario_base', 'auxilio_transporte', 'valor_horas_extra_diurnas',
        'valor_horas_extra_nocturnas', 'total_devengado', 'salud_empleado',
        'pension_empleado', 'total_deducido', 'salud_empresa', 'pension_empresa',
        'arl', 'caja_compensacion', 'sena', 'icbf', 'neto_pagar', 'created_at',
    ]

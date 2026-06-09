from django.contrib import admin
from .models import CuentaPUC, AsientoContable, MovimientoContable


@admin.register(CuentaPUC)
class CuentaPUCAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'nivel', 'activa', 'permite_movimiento']
    list_filter = ['tipo', 'nivel', 'activa']
    search_fields = ['codigo', 'nombre']
    ordering = ['codigo']


class MovimientoContableInline(admin.TabularInline):
    model = MovimientoContable
    extra = 2
    fields = ['cuenta', 'descripcion', 'debito', 'credito']


@admin.register(AsientoContable)
class AsientoContableAdmin(admin.ModelAdmin):
    list_display = ['pk', 'fecha', 'descripcion', 'es_manual', 'esta_cuadrado']
    list_filter = ['es_manual', 'fecha']
    inlines = [MovimientoContableInline]
    readonly_fields = ['created_at']

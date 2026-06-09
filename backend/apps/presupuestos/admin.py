from django.contrib import admin
from .models import Cotizacion, DetalleCotizacion, Presupuesto, ItemPresupuesto


class DetalleCotizacionInline(admin.TabularInline):
    model = DetalleCotizacion
    extra = 1
    readonly_fields = ['subtotal', 'iva_valor', 'total']


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'tercero', 'fecha', 'total', 'estado']
    list_filter = ['estado']
    search_fields = ['numero', 'tercero__nombre']
    readonly_fields = ['numero', 'subtotal', 'iva', 'total', 'created_at']
    inlines = [DetalleCotizacionInline]


class ItemPresupuestoInline(admin.TabularInline):
    model = ItemPresupuesto
    extra = 1


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'periodo_inicio', 'periodo_fin', 'estado']
    list_filter = ['estado']
    inlines = [ItemPresupuestoInline]

from django.contrib import admin
from .models import Factura, DetalleFactura


class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 1
    readonly_fields = ['subtotal', 'iva_valor', 'total']


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'tipo', 'tercero', 'fecha', 'total', 'estado']
    list_filter = ['tipo', 'estado', 'fecha']
    search_fields = ['numero', 'tercero__nombre']
    readonly_fields = ['numero', 'subtotal', 'iva', 'descuento', 'total', 'created_at']
    inlines = [DetalleFacturaInline]

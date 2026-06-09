from django.contrib import admin
from .models import CuentaPorCobrar, CuentaPorPagar, PagoRecibido, PagoRealizado


class PagoRecibidoInline(admin.TabularInline):
    model = PagoRecibido
    extra = 0
    readonly_fields = ['created_at']


class PagoRealizadoInline(admin.TabularInline):
    model = PagoRealizado
    extra = 0
    readonly_fields = ['created_at']


@admin.register(CuentaPorCobrar)
class CuentaPorCobrarAdmin(admin.ModelAdmin):
    list_display = ['factura', 'tercero', 'valor_total', 'valor_pagado', 'valor_pendiente', 'fecha_vencimiento', 'estado']
    list_filter = ['estado']
    readonly_fields = ['valor_pagado', 'valor_pendiente', 'created_at']
    inlines = [PagoRecibidoInline]


@admin.register(CuentaPorPagar)
class CuentaPorPagarAdmin(admin.ModelAdmin):
    list_display = ['factura', 'tercero', 'valor_total', 'valor_pagado', 'valor_pendiente', 'fecha_vencimiento', 'estado']
    list_filter = ['estado']
    readonly_fields = ['valor_pagado', 'valor_pendiente', 'created_at']
    inlines = [PagoRealizadoInline]

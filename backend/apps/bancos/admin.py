from django.contrib import admin
from .models import (
    CuentaBancaria, ExtractoBancario, MovimientoBancario,
    ConciliacionBancaria, PartidaConciliacion,
)


@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'banco', 'numero_cuenta', 'tipo', 'saldo_actual', 'activa']
    list_filter = ['tipo', 'activa', 'banco']
    search_fields = ['nombre', 'banco', 'numero_cuenta']


@admin.register(ExtractoBancario)
class ExtractoBancarioAdmin(admin.ModelAdmin):
    list_display = ['cuenta', 'periodo_inicio', 'periodo_fin', 'saldo_final_extracto', 'estado']
    list_filter = ['estado', 'cuenta']
    search_fields = ['cuenta__nombre']


@admin.register(MovimientoBancario)
class MovimientoBancarioAdmin(admin.ModelAdmin):
    list_display = ['extracto', 'fecha', 'descripcion', 'tipo', 'valor', 'conciliado']
    list_filter = ['tipo', 'conciliado']
    search_fields = ['descripcion', 'referencia']


@admin.register(ConciliacionBancaria)
class ConciliacionBancariaAdmin(admin.ModelAdmin):
    list_display = ['cuenta', 'periodo', 'saldo_extracto', 'saldo_libros', 'diferencia', 'estado']
    list_filter = ['estado', 'cuenta']


@admin.register(PartidaConciliacion)
class PartidaConciliacionAdmin(admin.ModelAdmin):
    list_display = ['conciliacion', 'tipo', 'descripcion', 'fecha', 'valor', 'afecta', 'resuelta']
    list_filter = ['tipo', 'afecta', 'resuelta']
    search_fields = ['descripcion']

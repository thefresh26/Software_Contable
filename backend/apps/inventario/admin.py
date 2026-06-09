from django.contrib import admin
from .models import Categoria, Producto, MovimientoInventario


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'precio_venta', 'stock_actual', 'activo']
    list_filter = ['activo', 'categoria']
    search_fields = ['codigo', 'nombre']


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tipo', 'cantidad', 'stock_nuevo', 'fecha']
    list_filter = ['tipo']
    readonly_fields = ['fecha']

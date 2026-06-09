from django.contrib import admin
from .models import CategoriaActivo, ActivoFijo, DepreciacionMensual, BajaActivo


@admin.register(CategoriaActivo)
class CategoriaActivoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'vida_util_años', 'metodo_depreciacion']
    list_filter = ['metodo_depreciacion']
    search_fields = ['nombre']


@admin.register(ActivoFijo)
class ActivoFijoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'valor_compra', 'valor_depreciado_acumulado', 'valor_en_libros', 'estado']
    list_filter = ['estado', 'categoria', 'metodo_depreciacion']
    search_fields = ['codigo', 'nombre', 'numero_serie']
    readonly_fields = ['valor_en_libros']


@admin.register(DepreciacionMensual)
class DepreciacionMensualAdmin(admin.ModelAdmin):
    list_display = ['activo', 'periodo', 'valor_depreciacion', 'valor_acumulado', 'valor_en_libros', 'aplicada']
    list_filter = ['aplicada', 'periodo']
    search_fields = ['activo__codigo', 'activo__nombre']


@admin.register(BajaActivo)
class BajaActivoAdmin(admin.ModelAdmin):
    list_display = ['activo', 'fecha', 'motivo', 'valor_venta', 'utilidad_perdida']
    search_fields = ['activo__codigo', 'activo__nombre']

from django.contrib import admin
from .models import Empresa, UsuarioEmpresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'ciudad', 'regimen', 'activa']
    search_fields = ['nombre', 'nit', 'razon_social']
    list_filter = ['regimen', 'activa']


@admin.register(UsuarioEmpresa)
class UsuarioEmpresaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'empresa', 'rol', 'activo', 'fecha_ingreso']
    list_filter = ['rol', 'activo', 'empresa']
    search_fields = ['usuario__username', 'empresa__nombre']

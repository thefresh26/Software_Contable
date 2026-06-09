from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'empresa', 'nit_empresa', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Empresa', {'fields': ('empresa', 'nit_empresa', 'logo')}),
    )

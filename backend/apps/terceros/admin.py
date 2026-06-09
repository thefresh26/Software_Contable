from django.contrib import admin
from .models import Tercero


@admin.register(Tercero)
class TerceroAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'tipo', 'tipo_persona', 'ciudad', 'activo']
    list_filter = ['tipo', 'tipo_persona', 'activo']
    search_fields = ['nombre', 'nit', 'email']

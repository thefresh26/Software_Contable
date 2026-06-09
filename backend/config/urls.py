from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.core.urls')),
    path('api/empresas/', include('apps.empresas.urls')),
    path('api/terceros/', include('apps.terceros.urls')),
    path('api/inventario/', include('apps.inventario.urls')),
    path('api/facturacion/', include('apps.facturacion.urls')),
    path('api/contabilidad/', include('apps.contabilidad.urls')),
    path('api/nomina/', include('apps.nomina.urls')),
    path('api/presupuestos/', include('apps.presupuestos.urls')),
    path('api/cartera/', include('apps.cartera.urls')),
    path('api/importador/', include('apps.importador.urls')),
    path('api/activos/', include('apps.activos.urls')),
    path('api/notificaciones/', include('apps.notificaciones.urls')),
    path('api/bancos/', include('apps.bancos.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

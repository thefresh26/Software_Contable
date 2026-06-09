from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacturaViewSet, DetalleFacturaViewSet, TipoRetencionViewSet

router = DefaultRouter()
router.register(r'facturas', FacturaViewSet, basename='factura')
router.register(r'detalles', DetalleFacturaViewSet, basename='detalle-factura')
router.register(r'retenciones-tipo', TipoRetencionViewSet, basename='tipo-retencion')

urlpatterns = [path('', include(router.urls))]

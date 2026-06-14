from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentaPUCViewSet, AsientoContableViewSet, CentroCostoViewSet, CierrePeriodoViewSet

router = DefaultRouter()
router.register(r'cuentas', CuentaPUCViewSet, basename='cuenta-puc')
router.register(r'asientos', AsientoContableViewSet, basename='asiento')
router.register(r'centros-costo', CentroCostoViewSet, basename='centro-costo')
router.register(r'cierres', CierrePeriodoViewSet, basename='cierre-periodo')

urlpatterns = [path('', include(router.urls))]

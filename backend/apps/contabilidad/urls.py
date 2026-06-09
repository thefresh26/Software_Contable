from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentaPUCViewSet, AsientoContableViewSet, CentroCostoViewSet

router = DefaultRouter()
router.register(r'cuentas', CuentaPUCViewSet, basename='cuenta-puc')
router.register(r'asientos', AsientoContableViewSet, basename='asiento')
router.register(r'centros-costo', CentroCostoViewSet, basename='centro-costo')

urlpatterns = [
    path('', include(router.urls)),
    # Los reportes están como @action en AsientoContableViewSet:
    # GET /api/contabilidad/asientos/balance-general/
    # GET /api/contabilidad/asientos/estado-resultados/
    # GET /api/contabilidad/asientos/libro-diario/
    # GET /api/contabilidad/asientos/libro-mayor/
    # GET /api/contabilidad/asientos/balance-comprobacion/
]

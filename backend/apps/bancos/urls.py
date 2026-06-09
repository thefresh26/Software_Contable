from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CuentaBancariaViewSet, ExtractoBancarioViewSet, MovimientoBancarioViewSet,
    ConciliacionBancariaViewSet, PartidaConciliacionViewSet, ImportarExtractoView,
)

router = DefaultRouter()
router.register(r'cuentas', CuentaBancariaViewSet, basename='cuenta-bancaria')
router.register(r'extractos', ExtractoBancarioViewSet, basename='extracto-bancario')
router.register(r'movimientos', MovimientoBancarioViewSet, basename='movimiento-bancario')
router.register(r'conciliaciones', ConciliacionBancariaViewSet, basename='conciliacion-bancaria')
router.register(r'partidas', PartidaConciliacionViewSet, basename='partida-conciliacion')

urlpatterns = [
    path('extractos/importar/', ImportarExtractoView.as_view(), name='importar-extracto'),
    path('', include(router.urls)),
    # Acciones extra registradas por los routers:
    # GET  /api/bancos/cuentas/{id}/saldo/
    # GET  /api/bancos/extractos/{id}/movimientos/
    # POST /api/bancos/movimientos/{id}/conciliar/
    # POST /api/bancos/movimientos/{id}/desconciliar/
    # POST /api/bancos/conciliaciones/{id}/conciliar-automatico/
    # POST /api/bancos/conciliaciones/{id}/finalizar/
    # GET  /api/bancos/conciliaciones/{id}/reporte/
    # GET/POST /api/bancos/conciliaciones/{id}/partidas/
]

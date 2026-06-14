from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentaPorCobrarViewSet, CuentaPorPagarViewSet
from .exports import ExportarPorCobrarView, ExportarPorPagarView

router = DefaultRouter()
router.register(r'por-cobrar', CuentaPorCobrarViewSet, basename='cxc')
router.register(r'por-pagar', CuentaPorPagarViewSet, basename='cxp')

urlpatterns = [
    path('', include(router.urls)),
    path('resumen/', CuentaPorCobrarViewSet.as_view({'get': 'resumen'}), name='cartera-resumen'),
    path('exportar/por-cobrar/', ExportarPorCobrarView.as_view(), name='exportar-por-cobrar'),
    path('exportar/por-pagar/', ExportarPorPagarView.as_view(), name='exportar-por-pagar'),
]

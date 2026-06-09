from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentaPorCobrarViewSet, CuentaPorPagarViewSet

router = DefaultRouter()
router.register(r'por-cobrar', CuentaPorCobrarViewSet, basename='cxc')
router.register(r'por-pagar', CuentaPorPagarViewSet, basename='cxp')

urlpatterns = [
    path('', include(router.urls)),
    path('resumen/', CuentaPorCobrarViewSet.as_view({'get': 'resumen'}), name='cartera-resumen'),
]

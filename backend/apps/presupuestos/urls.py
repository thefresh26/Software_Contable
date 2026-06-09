from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CotizacionViewSet, PresupuestoViewSet

router = DefaultRouter()
router.register(r'cotizaciones', CotizacionViewSet, basename='cotizacion')
router.register(r'presupuestos', PresupuestoViewSet, basename='presupuesto')

urlpatterns = [path('', include(router.urls))]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpleadoViewSet, LiquidacionNominaViewSet, LiquidarNominaView
from .exports import ExportarLiquidacionesView

router = DefaultRouter()
router.register(r'empleados', EmpleadoViewSet, basename='empleado')
router.register(r'liquidaciones', LiquidacionNominaViewSet, basename='liquidacion')

urlpatterns = [
    path('', include(router.urls)),
    path('liquidar/', LiquidarNominaView.as_view({'post': 'liquidar'}), name='liquidar-nomina'),
    path('exportar/liquidaciones/', ExportarLiquidacionesView.as_view(), name='exportar-liquidaciones'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaActivoViewSet, ActivoFijoViewSet
from .exports import ExportarActivosView

router = DefaultRouter()
router.register(r'categorias', CategoriaActivoViewSet, basename='categoria-activo')
router.register(r'', ActivoFijoViewSet, basename='activo-fijo')

urlpatterns = [
    path('exportar/', ExportarActivosView.as_view(), name='exportar-activos'),
    path('', include(router.urls)),
]

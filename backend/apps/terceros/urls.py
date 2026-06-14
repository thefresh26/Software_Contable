from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TerceroViewSet
from .exports import ExportarTercerosView

router = DefaultRouter()
router.register(r'', TerceroViewSet, basename='tercero')

urlpatterns = [
    path('', include(router.urls)),
    path('exportar/', ExportarTercerosView.as_view(), name='exportar-terceros'),
]

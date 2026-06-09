from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaActivoViewSet, ActivoFijoViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaActivoViewSet, basename='categoria-activo')
router.register(r'', ActivoFijoViewSet, basename='activo-fijo')

urlpatterns = [path('', include(router.urls))]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, RefreshView, MeView, RegistroView, UsuarioViewSet, HistorialCambioViewSet, ValidarNITView

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'historial', HistorialCambioViewSet, basename='historial-cambio')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('validar-nit/', ValidarNITView.as_view(), name='validar-nit'),
    path('', include(router.urls)),
]

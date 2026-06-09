from django.urls import path
from .views import (
    ImportarTercerosView, ImportarProductosView,
    ImportarPlanCuentasView, PlantillaExcelView,
)

urlpatterns = [
    path('terceros/', ImportarTercerosView.as_view(), name='importar-terceros'),
    path('productos/', ImportarProductosView.as_view(), name='importar-productos'),
    path('plan-cuentas/', ImportarPlanCuentasView.as_view(), name='importar-plan-cuentas'),
    path('plantilla/<str:tipo>/', PlantillaExcelView.as_view(), name='plantilla-excel'),
]

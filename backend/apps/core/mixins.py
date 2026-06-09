from rest_framework.exceptions import PermissionDenied


class RolRequeridoMixin:
    """Restringe el acceso a un viewset según el rol del usuario."""
    roles_permitidos = []

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.roles_permitidos and request.user.is_authenticated:
            if request.user.rol not in self.roles_permitidos and not request.user.is_superuser:
                raise PermissionDenied('No tiene permisos para esta sección.')

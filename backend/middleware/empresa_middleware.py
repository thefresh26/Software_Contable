class EmpresaMiddleware:
    """Inyecta la empresa activa del usuario en cada request como request.empresa_activa."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa_activa = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.empresa_activa = getattr(request.user, 'empresa_activa', None)
        return self.get_response(request)

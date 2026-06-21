class EmpresaMiddleware:
    """Inyecta la empresa activa del usuario en cada request como request.empresa_activa.

    request.user en este punto de la cadena de middleware todavia es el
    AnonymousUser de sesion: la autenticacion JWT de DRF solo resuelve
    request.user de forma perezosa, dentro del dispatch de la vista (es
    decir, despues de que corre este middleware). Por eso no podemos leer
    request.user aqui; en su lugar autenticamos el JWT directamente con el
    mismo backend que usan las vistas, para obtener el usuario real (o
    None) de forma sincrona, sin envoltorios perezosos que rompan los
    chequeos `is None`/`isinstance` que usa el ORM de Django.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa_activa = None
        usuario = self._usuario_jwt(request)
        if usuario is not None:
            request.empresa_activa = getattr(usuario, 'empresa_activa', None)
        return self.get_response(request)

    @staticmethod
    def _usuario_jwt(request):
        from rest_framework_simplejwt.authentication import JWTAuthentication
        try:
            resultado = JWTAuthentication().authenticate(request)
        except Exception:
            return None
        if resultado is None:
            return None
        usuario, _token = resultado
        return usuario

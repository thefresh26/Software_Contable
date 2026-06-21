from django.utils.functional import SimpleLazyObject


class EmpresaMiddleware:
    """Inyecta la empresa activa del usuario en cada request como request.empresa_activa.

    request.user en este punto de la cadena de middleware todavia es el
    AnonymousUser de sesion (la autenticacion JWT de DRF solo resuelve
    request.user de forma perezosa, dentro del dispatch de la vista). Por
    eso la resolucion se envuelve en SimpleLazyObject: para entonces ya se
    habra resuelto el usuario real via DRF y request.user reflejara el JWT.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa_activa = SimpleLazyObject(lambda: self._resolver(request))
        return self.get_response(request)

    @staticmethod
    def _resolver(request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            return getattr(user, 'empresa_activa', None)
        return None

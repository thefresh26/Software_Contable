class EmpresaFilterMixin:
    """
    Filtra automáticamente los querysets por empresa activa del usuario.
    Agregar como primer padre en todos los ViewSets.
    """

    def _model_tiene_empresa(self, model):
        try:
            model._meta.get_field('empresa')
            return True
        except Exception:
            return False

    def get_queryset(self):
        qs = super().get_queryset()
        empresa = getattr(self.request, 'empresa_activa', None)
        if empresa and self._model_tiene_empresa(qs.model):
            return qs.filter(empresa=empresa)
        return qs

    def perform_create(self, serializer):
        empresa = getattr(self.request, 'empresa_activa', None)
        if empresa:
            serializer.save(empresa=empresa)
        else:
            super().perform_create(serializer)

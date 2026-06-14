from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver


def _registrar(instance, accion, modelo_nombre, empresa=None, usuario=None):
    """Registra un HistorialCambio. Se importa dentro de la función para evitar importaciones circulares."""
    try:
        from apps.core.models import HistorialCambio
        try:
            from django_currentuser.middleware import get_current_authenticated_user
            usuario = usuario or get_current_authenticated_user()
        except Exception:
            pass
        HistorialCambio.objects.create(
            empresa=empresa or getattr(instance, 'empresa', None),
            usuario=usuario,
            accion=accion,
            modelo=modelo_nombre,
            objeto_id=instance.pk,
            objeto_repr=str(instance)[:200],
            cambios={},
        )
    except Exception:
        pass


def registrar_auditoria(instance, created, modelo_nombre):
    _registrar(instance, 'crear' if created else 'editar', modelo_nombre)


def registrar_eliminacion(instance, modelo_nombre):
    _registrar(instance, 'eliminar', modelo_nombre)


# ── Signals ──────────────────────────────────────────────────────────────────

def conectar_signals():
    from apps.facturacion.models import Factura
    from apps.terceros.models import Tercero
    from apps.inventario.models import Producto
    from apps.nomina.models import Empleado
    from apps.contabilidad.models import AsientoContable

    @receiver(post_save, sender=Factura, dispatch_uid='audit_factura_save')
    def audit_factura(sender, instance, created, **kwargs):
        registrar_auditoria(instance, created, 'Factura')

    @receiver(pre_delete, sender=Factura, dispatch_uid='audit_factura_delete')
    def audit_factura_delete(sender, instance, **kwargs):
        registrar_eliminacion(instance, 'Factura')

    @receiver(post_save, sender=Tercero, dispatch_uid='audit_tercero_save')
    def audit_tercero(sender, instance, created, **kwargs):
        registrar_auditoria(instance, created, 'Tercero')

    @receiver(pre_delete, sender=Tercero, dispatch_uid='audit_tercero_delete')
    def audit_tercero_delete(sender, instance, **kwargs):
        registrar_eliminacion(instance, 'Tercero')

    @receiver(post_save, sender=Producto, dispatch_uid='audit_producto_save')
    def audit_producto(sender, instance, created, **kwargs):
        registrar_auditoria(instance, created, 'Producto')

    @receiver(post_save, sender=Empleado, dispatch_uid='audit_empleado_save')
    def audit_empleado(sender, instance, created, **kwargs):
        registrar_auditoria(instance, created, 'Empleado')

    @receiver(post_save, sender=AsientoContable, dispatch_uid='audit_asiento_save')
    def audit_asiento(sender, instance, created, **kwargs):
        registrar_auditoria(instance, created, 'AsientoContable')

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver


def _registrar(instance, accion, modelo_nombre, empresa=None, usuario=None):
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


# ── Signals definidos a nivel de módulo para evitar recolección por GC ────────

def conectar_signals():
    from apps.facturacion.models import Factura
    from apps.terceros.models import Tercero
    from apps.inventario.models import Producto
    from apps.nomina.models import Empleado
    from apps.contabilidad.models import AsientoContable

    post_save.connect(_audit_factura, sender=Factura, dispatch_uid='audit_factura_save', weak=False)
    pre_delete.connect(_audit_factura_delete, sender=Factura, dispatch_uid='audit_factura_delete', weak=False)
    post_save.connect(_audit_tercero, sender=Tercero, dispatch_uid='audit_tercero_save', weak=False)
    pre_delete.connect(_audit_tercero_delete, sender=Tercero, dispatch_uid='audit_tercero_delete', weak=False)
    post_save.connect(_audit_producto, sender=Producto, dispatch_uid='audit_producto_save', weak=False)
    post_save.connect(_audit_empleado, sender=Empleado, dispatch_uid='audit_empleado_save', weak=False)
    post_save.connect(_audit_asiento, sender=AsientoContable, dispatch_uid='audit_asiento_save', weak=False)


def _audit_factura(sender, instance, created, **kwargs):
    registrar_auditoria(instance, created, 'Factura')


def _audit_factura_delete(sender, instance, **kwargs):
    registrar_eliminacion(instance, 'Factura')


def _audit_tercero(sender, instance, created, **kwargs):
    registrar_auditoria(instance, created, 'Tercero')


def _audit_tercero_delete(sender, instance, **kwargs):
    registrar_eliminacion(instance, 'Tercero')


def _audit_producto(sender, instance, created, **kwargs):
    registrar_auditoria(instance, created, 'Producto')


def _audit_empleado(sender, instance, created, **kwargs):
    registrar_auditoria(instance, created, 'Empleado')


def _audit_asiento(sender, instance, created, **kwargs):
    registrar_auditoria(instance, created, 'AsientoContable')

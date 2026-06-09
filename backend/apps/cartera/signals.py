from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PagoRecibido


@receiver(post_save, sender=PagoRecibido)
def notificar_pago_recibido(sender, instance, created, **kwargs):
    if not created:
        return
    from apps.core.models import Usuario
    from apps.notificaciones.services import crear_notificacion
    for usuario in Usuario.objects.filter(is_active=True):
        crear_notificacion(
            usuario=usuario,
            tipo='pago_recibido',
            titulo='Pago recibido',
            mensaje=f'Se registró un pago de ${instance.valor:,.0f} para la factura {instance.cuenta_cobrar.factura.numero}',
            prioridad='baja',
            url_accion='/cartera/por-cobrar',
            objeto_id=instance.cuenta_cobrar_id,
        )

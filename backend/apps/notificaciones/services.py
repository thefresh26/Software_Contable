from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import Notificacion, ConfiguracionNotificacion


# â”€â”€â”€ NotificaciÃ³n + email â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def crear_notificacion(usuario, tipo, titulo, mensaje, prioridad='media', url_accion='', objeto_id=None):
    """Crea notificaciÃ³n en el sistema y envÃ­a email si estÃ¡ configurado."""
    notif = Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        prioridad=prioridad,
        url_accion=url_accion,
        objeto_id=objeto_id,
    )
    config = ConfiguracionNotificacion.objects.get_or_create(usuario=usuario)[0]
    if debe_enviar_email(tipo, config):
        enviar_email_notificacion(notif)
    return notif


_TIPO_CONFIG_EMAIL = {
    'factura_vencer': 'email_facturas_vencer',
    'factura_vencida': 'email_facturas_vencidas',
    'stock_bajo': 'email_stock_bajo',
    'pago_recibido': 'email_pagos',
    'pago_realizado': 'email_pagos',
    'nomina_pendiente': 'email_nomina',
    'cotizacion_vencer': 'email_cotizaciones',
}


def debe_enviar_email(tipo, config):
    """Determina si, segÃºn las preferencias del usuario, debe enviarse un email para este tipo."""
    campo = _TIPO_CONFIG_EMAIL.get(tipo)
    if campo is None:
        return False
    return getattr(config, campo, False)


_TIPO_TEMPLATE = {
    'factura_vencer': 'emails/facturas_por_vencer.html',
    'stock_bajo': 'emails/stock_bajo.html',
    'pago_recibido': 'emails/pago_recibido.html',
    'cotizacion_vencer': 'emails/cotizacion_por_vencer.html',
    'nomina_pendiente': 'emails/nomina_pendiente.html',
}


def enviar_email_notificacion(notif, contexto=None):
    """Renderiza la plantilla correspondiente al tipo de notificaciÃ³n y envÃ­a el correo."""
    template = _TIPO_TEMPLATE.get(notif.tipo)
    if not template:
        return
    ctx = {'usuario': notif.usuario, **(contexto or {})}
    html = render_to_string(template, ctx)
    send_mail(
        subject=notif.titulo,
        message=notif.mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[notif.usuario.email] if notif.usuario.email else [],
        html_message=html,
        fail_silently=True,
    )
    notif.email_enviado = True
    notif.save(update_fields=['email_enviado'])


# â”€â”€â”€ VerificaciÃ³n de alertas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def verificar_alertas():
    """
    FunciÃ³n principal que verifica todas las condiciones de alerta.
    Debe llamarse diariamente (con un cron o management command).
    """
    verificar_facturas_por_vencer()
    verificar_facturas_vencidas()
    verificar_stock_bajo()
    verificar_cotizaciones_por_vencer()
    verificar_nomina_pendiente()
    verificar_activos_depreciados()


def _ya_notificado_hoy(usuario, tipo, hoy):
    return Notificacion.objects.filter(usuario=usuario, tipo=tipo, created_at__date=hoy).exists()


def verificar_facturas_por_vencer():
    from apps.facturacion.models import Factura
    from apps.core.models import Usuario
    hoy = timezone.localdate()
    for usuario in Usuario.objects.filter(is_active=True):
        config = ConfiguracionNotificacion.objects.get_or_create(usuario=usuario)[0]
        dias = config.dias_anticipacion_factura
        fecha_limite = hoy + timedelta(days=dias)
        facturas = Factura.objects.filter(
            tipo='FV',
            estado='emitida',
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=fecha_limite,
        )
        if facturas.exists() and not _ya_notificado_hoy(usuario, 'factura_vencer', hoy):
            crear_notificacion(
                usuario=usuario,
                tipo='factura_vencer',
                titulo=f'{facturas.count()} factura(s) por vencer',
                mensaje=f'Tienes {facturas.count()} facturas que vencen en los prÃ³ximos {dias} dÃ­as.',
                prioridad='alta',
                url_accion='/cartera/por-cobrar',
            )


def verificar_facturas_vencidas():
    from apps.facturacion.models import Factura
    from apps.core.models import Usuario
    hoy = timezone.localdate()
    for usuario in Usuario.objects.filter(is_active=True):
        facturas = Factura.objects.filter(
            tipo='FV',
            estado='emitida',
            fecha_vencimiento__lt=hoy,
        )
        if facturas.exists() and not _ya_notificado_hoy(usuario, 'factura_vencida', hoy):
            crear_notificacion(
                usuario=usuario,
                tipo='factura_vencida',
                titulo=f'{facturas.count()} factura(s) vencida(s)',
                mensaje=f'Tienes {facturas.count()} facturas vencidas sin pagar.',
                prioridad='critica',
                url_accion='/cartera/por-cobrar',
            )


def verificar_stock_bajo():
    from apps.inventario.models import Producto
    from django.db.models import F
    from apps.core.models import Usuario
    hoy = timezone.localdate()
    productos = Producto.objects.filter(stock_actual__lte=F('stock_minimo'))
    if not productos.exists():
        return
    for usuario in Usuario.objects.filter(is_active=True):
        if not _ya_notificado_hoy(usuario, 'stock_bajo', hoy):
            crear_notificacion(
                usuario=usuario,
                tipo='stock_bajo',
                titulo=f'{productos.count()} producto(s) con stock bajo',
                mensaje=f'Hay {productos.count()} productos por debajo del stock mÃ­nimo.',
                prioridad='alta',
                url_accion='/inventario',
            )


def verificar_cotizaciones_por_vencer():
    from apps.presupuestos.models import Cotizacion
    from apps.core.models import Usuario
    hoy = timezone.localdate()
    for usuario in Usuario.objects.filter(is_active=True):
        config = ConfiguracionNotificacion.objects.get_or_create(usuario=usuario)[0]
        dias = config.dias_anticipacion_cotizacion
        fecha_limite = hoy + timedelta(days=dias)
        cotizaciones = Cotizacion.objects.filter(
            estado='enviada',
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=fecha_limite,
        )
        if cotizaciones.exists() and not _ya_notificado_hoy(usuario, 'cotizacion_vencer', hoy):
            crear_notificacion(
                usuario=usuario,
                tipo='cotizacion_vencer',
                titulo=f'{cotizaciones.count()} cotizaciÃ³n(es) por vencer',
                mensaje=f'Tienes {cotizaciones.count()} cotizaciones que vencen en los prÃ³ximos {dias} dÃ­as.',
                prioridad='media',
                url_accion='/cotizaciones',
            )


def verificar_nomina_pendiente():
    from apps.nomina.models import Empleado, LiquidacionNomina
    from apps.core.models import Usuario
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    pendientes = Empleado.objects.filter(activo=True).exclude(
        liquidaciones__periodo_fin__gte=inicio_mes
    )
    if not pendientes.exists():
        return
    for usuario in Usuario.objects.filter(is_active=True):
        if not _ya_notificado_hoy(usuario, 'nomina_pendiente', hoy):
            crear_notificacion(
                usuario=usuario,
                tipo='nomina_pendiente',
                titulo=f'NÃ³mina pendiente: {pendientes.count()} empleado(s)',
                mensaje=f'{pendientes.count()} empleados no tienen liquidaciÃ³n registrada este mes.',
                prioridad='media',
                url_accion='/nomina/liquidar',
            )


def verificar_activos_depreciados():
    from apps.activos.models import ActivoFijo
    from apps.core.models import Usuario
    hoy = timezone.localdate()
    activos = ActivoFijo.objects.filter(estado='activo')
    proximos = [a for a in activos if a.porcentaje_depreciado >= 90]
    if not proximos:
        return
    for usuario in Usuario.objects.filter(is_active=True):
        if not _ya_notificado_hoy(usuario, 'activo_depreciado', hoy):
            crear_notificacion(
                usuario=usuario,
                tipo='activo_depreciado',
                titulo=f'{len(proximos)} activo(s) prÃ³ximos a depreciarse totalmente',
                mensaje=f'{len(proximos)} activos superan el 90% de su depreciaciÃ³n.',
                prioridad='media',
                url_accion='/activos/reportes',
            )

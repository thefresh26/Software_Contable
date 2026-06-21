"""
Operaciones de negocio al emitir/anular facturas:
- Actualizar stock
- Generar asiento contable (incluyendo retenciones)
- Crear CuentaPorCobrar / CuentaPorPagar en cartera
"""
from decimal import Decimal
from django.db import transaction


# ─── Stock ────────────────────────────────────────────────────────────────────

def actualizar_stock_emision(factura):
    from apps.inventario.models import MovimientoInventario
    tipo_mov = 'salida' if factura.tipo == 'FV' else 'entrada'
    for detalle in factura.detalles.select_related('producto').all():
        producto = detalle.producto
        if producto is None:
            continue  # ítem de servicio sin producto físico
        cantidad = int(detalle.cantidad)
        stock_anterior = producto.stock_actual
        if tipo_mov == 'salida':
            if producto.stock_actual < cantidad:
                raise ValueError(f'Stock insuficiente para {producto}: disponible {producto.stock_actual}')
            producto.stock_actual -= cantidad
        else:
            producto.stock_actual += cantidad
        producto.save(update_fields=['stock_actual'])
        MovimientoInventario.objects.create(
            producto=producto, tipo=tipo_mov, cantidad=cantidad,
            stock_anterior=stock_anterior, stock_nuevo=producto.stock_actual,
            motivo=f'{"Venta" if tipo_mov == "salida" else "Compra"} — {factura.numero}',
            factura=factura,
        )


def revertir_stock_anulacion(factura):
    from apps.inventario.models import MovimientoInventario
    tipo_mov = 'entrada' if factura.tipo == 'FV' else 'salida'
    for detalle in factura.detalles.select_related('producto').all():
        producto = detalle.producto
        if producto is None:
            continue
        cantidad = int(detalle.cantidad)
        stock_anterior = producto.stock_actual
        if tipo_mov == 'salida':
            if producto.stock_actual < cantidad:
                raise ValueError(f'Stock insuficiente al revertir {producto}')
            producto.stock_actual -= cantidad
        else:
            producto.stock_actual += cantidad
        producto.save(update_fields=['stock_actual'])
        MovimientoInventario.objects.create(
            producto=producto, tipo='ajuste',
            cantidad=-cantidad if factura.tipo == 'FV' else cantidad,
            stock_anterior=stock_anterior, stock_nuevo=producto.stock_actual,
            motivo=f'Anulación — {factura.numero}', factura=factura,
        )


# ─── Asientos contables ────────────────────────────────────────────────────────

def generar_asiento_factura_venta(factura):
    from apps.contabilidad.models import CuentaPUC, AsientoContable, MovimientoContable
    clientes = CuentaPUC.objects.filter(codigo='1305').first()
    ingresos = CuentaPUC.objects.filter(codigo='4135').first()
    iva_pagar = CuentaPUC.objects.filter(codigo='2408').first()
    if not all([clientes, ingresos, iva_pagar]):
        return

    asiento = AsientoContable.objects.create(
        empresa=factura.empresa,
        fecha=factura.fecha,
        descripcion=f'Factura de venta {factura.numero} — {factura.tercero}',
        factura=factura, es_manual=False,
    )
    movimientos = [
        MovimientoContable(asiento=asiento, cuenta=clientes,
                           descripcion='Cuentas por cobrar', debito=factura.total, credito=0),
        MovimientoContable(asiento=asiento, cuenta=ingresos,
                           descripcion='Ingresos por ventas', debito=0, credito=factura.subtotal),
        MovimientoContable(asiento=asiento, cuenta=iva_pagar,
                           descripcion='IVA generado', debito=0, credito=factura.iva),
    ]
    MovimientoContable.objects.bulk_create(movimientos)


def generar_asiento_factura_compra(factura):
    from apps.contabilidad.models import CuentaPUC, AsientoContable, MovimientoContable
    inventarios = CuentaPUC.objects.filter(codigo='1435').first()
    iva_desc = CuentaPUC.objects.filter(codigo='2408').first()
    proveedores = CuentaPUC.objects.filter(codigo='2205').first()
    if not all([inventarios, iva_desc, proveedores]):
        return

    retenciones = list(factura.retenciones.select_related('tipo_retencion__cuenta_contable').all())
    total_retenciones = sum(r.valor for r in retenciones)
    neto_pagar = factura.total - total_retenciones

    asiento = AsientoContable.objects.create(
        empresa=factura.empresa,
        fecha=factura.fecha,
        descripcion=f'Factura de compra {factura.numero} — {factura.tercero}',
        factura=factura, es_manual=False,
    )
    movimientos = [
        MovimientoContable(asiento=asiento, cuenta=inventarios,
                           descripcion='Compra mercancía', debito=factura.subtotal, credito=0),
        MovimientoContable(asiento=asiento, cuenta=iva_desc,
                           descripcion='IVA descontable', debito=factura.iva, credito=0),
    ]
    # Mapeo de tipo de retención → código PUC estándar colombiano
    _CUENTA_FALLBACK = {
        'retefuente': '2365',
        'reteiva':    '2367',
        'reteica':    '2368',
    }

    # Una línea por cada retención (siempre incluir para que el asiento cuadre)
    for ret in retenciones:
        cuenta_ret = ret.tipo_retencion.cuenta_contable
        if not cuenta_ret:
            # Buscar cuenta PUC estándar según tipo
            codigo_fallback = _CUENTA_FALLBACK.get(ret.tipo_retencion.tipo)
            if codigo_fallback:
                cuenta_ret = CuentaPUC.objects.filter(codigo=codigo_fallback).first()
        if cuenta_ret:
            movimientos.append(
                MovimientoContable(asiento=asiento, cuenta=cuenta_ret,
                                   descripcion=f'Retención {ret.tipo_retencion.nombre}',
                                   debito=0, credito=ret.valor)
            )
        else:
            # Sin cuenta disponible: sumar al proveedor para no descuadrar
            neto_pagar += ret.valor

    movimientos.append(
        MovimientoContable(asiento=asiento, cuenta=proveedores,
                           descripcion='Cuentas por pagar (neto)', debito=0, credito=neto_pagar)
    )
    MovimientoContable.objects.bulk_create(movimientos)


# ─── Cartera ────────────────────────────────────────────────────────────────────

def crear_cuenta_cobrar(factura):
    """Al emitir FV → CuentaPorCobrar automática."""
    try:
        from apps.cartera.models import CuentaPorCobrar
        import datetime
        venc = factura.fecha_vencimiento or (factura.fecha + datetime.timedelta(days=30))
        CuentaPorCobrar.objects.get_or_create(
            factura=factura,
            defaults=dict(
                empresa=factura.empresa,
                tercero=factura.tercero,
                valor_total=factura.total,
                valor_pendiente=factura.total,
                fecha_vencimiento=venc,
            ),
        )
    except Exception:
        pass  # cartera puede no estar disponible


def crear_cuenta_pagar(factura):
    """Al emitir FC → CuentaPorPagar automática."""
    try:
        from apps.cartera.models import CuentaPorPagar
        import datetime
        total_ret = factura.total_retenciones
        neto = factura.total - total_ret
        venc = factura.fecha_vencimiento or (factura.fecha + datetime.timedelta(days=30))
        CuentaPorPagar.objects.get_or_create(
            factura=factura,
            defaults=dict(
                empresa=factura.empresa,
                tercero=factura.tercero,
                valor_total=neto,
                valor_pendiente=neto,
                fecha_vencimiento=venc,
            ),
        )
    except Exception:
        pass


# ─── Notificaciones ─────────────────────────────────────────────────────────────

def notificar_factura_emitida(factura):
    """Al emitir una factura, notifica a los usuarios activos."""
    try:
        from apps.core.models import Usuario
        from apps.notificaciones.services import crear_notificacion
        for usuario in Usuario.objects.filter(is_active=True):
            crear_notificacion(
                usuario=usuario,
                tipo='sistema',
                titulo=f'Factura {factura.numero} emitida',
                mensaje=f'Factura emitida a {factura.tercero.nombre} por ${factura.total:,.0f}',
                prioridad='baja',
                url_accion='/facturacion',
                objeto_id=factura.id,
            )
    except Exception:
        pass

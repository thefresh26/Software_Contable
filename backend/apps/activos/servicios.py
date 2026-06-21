"""
Operaciones de negocio sobre activos fijos:
- Generación de asientos contables de depreciación
- Aplicación (idempotente) de depreciación mensual
- Generación de asientos y registro de bajas de activos
"""
from decimal import Decimal
from django.db import transaction

from .models import ActivoFijo, DepreciacionMensual, BajaActivo
from .utils import calcular_dep_mensual


# ─── Depreciación ────────────────────────────────────────────────────────────

def generar_asiento_depreciacion(activo, periodo, valor_dep):
    from apps.contabilidad.models import CuentaPUC, AsientoContable, MovimientoContable

    cuenta_gasto = activo.cuenta_gasto_depreciacion or activo.categoria.cuenta_gasto_depreciacion \
        or CuentaPUC.objects.filter(codigo='5160').first()
    cuenta_dep_acum = activo.cuenta_depreciacion_acumulada or activo.categoria.cuenta_depreciacion \
        or CuentaPUC.objects.filter(codigo='1592').first()
    if not cuenta_gasto or not cuenta_dep_acum:
        return None

    asiento = AsientoContable.objects.create(
        empresa=activo.empresa,
        fecha=periodo,
        descripcion=f'Depreciación {periodo.strftime("%Y-%m")} — {activo.codigo} {activo.nombre}',
        es_manual=False,
    )
    MovimientoContable.objects.bulk_create([
        MovimientoContable(asiento=asiento, cuenta=cuenta_gasto,
                           descripcion=f'Gasto depreciación {activo.codigo}', debito=valor_dep, credito=0),
        MovimientoContable(asiento=asiento, cuenta=cuenta_dep_acum,
                           descripcion=f'Depreciación acumulada {activo.codigo}', debito=0, credito=valor_dep),
    ])
    return asiento


def aplicar_depreciacion(activo, periodo):
    """
    Aplica la depreciación de un período (primer día del mes) a un activo.
    Idempotente: si ya existe una depreciación aplicada para ese período no la duplica.
    Retorna (DepreciacionMensual|None, creado: bool)
    """
    existente = DepreciacionMensual.objects.filter(activo=activo, periodo=periodo, aplicada=True).first()
    if existente:
        return existente, False

    if activo.estado != 'activo':
        return None, False

    valor_dep = calcular_dep_mensual(activo, periodo)
    if valor_dep <= 0:
        return None, False

    with transaction.atomic():
        activo.valor_depreciado_acumulado = activo.valor_depreciado_acumulado + valor_dep
        activo.valor_en_libros = activo.valor_compra - activo.valor_depreciado_acumulado
        if activo.valor_en_libros <= activo.valor_residual:
            activo.estado = 'depreciado'
        activo.save()

        asiento = generar_asiento_depreciacion(activo, periodo, valor_dep)

        dep = DepreciacionMensual.objects.create(
            activo=activo,
            periodo=periodo,
            valor_depreciacion=valor_dep,
            valor_acumulado=activo.valor_depreciado_acumulado,
            valor_en_libros=activo.valor_en_libros,
            asiento=asiento,
            aplicada=True,
        )
    return dep, True


# ─── Baja de activos ─────────────────────────────────────────────────────────

def generar_asiento_baja(activo, fecha, valor_venta):
    """
    Genera el asiento contable de baja/venta de un activo según las reglas:
    - Sin venta: reversa depreciación acumulada, registra pérdida por el valor en libros,
      y retira el activo por su valor de compra.
    - Con venta: registra el ingreso, reversa depreciación acumulada, retira el activo
      por su valor de compra y registra la utilidad o pérdida según corresponda.
    Retorna (asiento, utilidad_perdida)
    """
    from apps.contabilidad.models import CuentaPUC, AsientoContable, MovimientoContable

    cuenta_activo = activo.cuenta_activo or activo.categoria.cuenta_activo
    cuenta_dep_acum = activo.cuenta_depreciacion_acumulada or activo.categoria.cuenta_depreciacion \
        or CuentaPUC.objects.filter(codigo='1592').first()
    if not cuenta_activo or not cuenta_dep_acum:
        return None, Decimal('0')

    valor_compra = activo.valor_compra
    dep_acumulada = activo.valor_depreciado_acumulado
    valor_libros = activo.valor_en_libros
    valor_venta = Decimal(str(valor_venta))

    asiento = AsientoContable.objects.create(
        empresa=activo.empresa,
        fecha=fecha,
        descripcion=f'Baja de activo {activo.codigo} — {activo.nombre}',
        es_manual=False,
    )
    movimientos = [
        MovimientoContable(asiento=asiento, cuenta=cuenta_dep_acum,
                           descripcion='Reverso depreciación acumulada', debito=dep_acumulada, credito=0),
    ]

    if valor_venta == 0:
        cuenta_perdida = CuentaPUC.objects.filter(codigo='5395').first()
        if cuenta_perdida and valor_libros > 0:
            movimientos.append(
                MovimientoContable(asiento=asiento, cuenta=cuenta_perdida,
                                   descripcion='Pérdida en baja de activo', debito=valor_libros, credito=0))
        movimientos.append(
            MovimientoContable(asiento=asiento, cuenta=cuenta_activo,
                               descripcion='Retiro del activo', debito=0, credito=valor_compra))
        utilidad_perdida = -valor_libros
    else:
        cuenta_caja = CuentaPUC.objects.filter(codigo='1110').first()
        if cuenta_caja:
            movimientos.append(
                MovimientoContable(asiento=asiento, cuenta=cuenta_caja,
                                   descripcion='Venta del activo', debito=valor_venta, credito=0))
        diferencia = valor_venta - valor_libros
        if diferencia > 0:
            cuenta_utilidad = CuentaPUC.objects.filter(codigo='4250').first()
            if cuenta_utilidad:
                movimientos.append(
                    MovimientoContable(asiento=asiento, cuenta=cuenta_utilidad,
                                       descripcion='Utilidad en venta de activo', debito=0, credito=diferencia))
        elif diferencia < 0:
            cuenta_perdida_venta = CuentaPUC.objects.filter(codigo='5320').first()
            if cuenta_perdida_venta:
                movimientos.append(
                    MovimientoContable(asiento=asiento, cuenta=cuenta_perdida_venta,
                                       descripcion='Pérdida en venta de activo', debito=-diferencia, credito=0))
        movimientos.append(
            MovimientoContable(asiento=asiento, cuenta=cuenta_activo,
                               descripcion='Retiro del activo', debito=0, credito=valor_compra))
        utilidad_perdida = diferencia

    MovimientoContable.objects.bulk_create(movimientos)
    return asiento, utilidad_perdida


def dar_baja_activo(activo, fecha, motivo, valor_venta=Decimal('0'), observaciones=''):
    """Da de baja un activo: cambia su estado, genera el asiento y registra la baja."""
    with transaction.atomic():
        asiento, utilidad_perdida = generar_asiento_baja(activo, fecha, valor_venta)
        baja = BajaActivo.objects.create(
            activo=activo,
            fecha=fecha,
            motivo=motivo,
            valor_venta=valor_venta,
            utilidad_perdida=utilidad_perdida,
            asiento=asiento,
            observaciones=observaciones,
        )
        activo.estado = 'vendido' if Decimal(str(valor_venta)) > 0 else 'dado_baja'
        activo.save(update_fields=['estado'])
    return baja

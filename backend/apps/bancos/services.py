import datetime
from decimal import Decimal

from django.db.models import Sum

MESES_ES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

# Categorías de partidas que afectan cada lado de la conciliación, en el orden
# y con las claves esperadas por el reporte de conciliación bancaria.
BUCKETS_EXTRACTO = [
    ('deposito_transito', 'depositos_en_transito', 'total_depositos_transito'),
    ('cheque_girado', 'cheques_girados_no_cobrados', 'total_cheques_pendientes'),
]
BUCKETS_LIBROS = [
    ('nota_debito', 'notas_debito_no_registradas', 'total_notas_debito'),
    ('nota_credito', 'notas_credito_no_registradas', 'total_notas_credito'),
    ('error_libros', 'errores_libros', 'total_errores_libros'),
]


def calcular_saldo_libros(cuenta_bancaria, fecha_inicio, fecha_fin):
    from apps.contabilidad.models import MovimientoContable
    movimientos = MovimientoContable.objects.filter(
        cuenta=cuenta_bancaria.cuenta_contable,
        asiento__fecha__gte=fecha_inicio,
        asiento__fecha__lte=fecha_fin,
    )
    totales = movimientos.aggregate(total_debito=Sum('debito'), total_credito=Sum('credito'))
    total_debitos = totales['total_debito'] or Decimal('0')
    total_creditos = totales['total_credito'] or Decimal('0')
    return cuenta_bancaria.saldo_inicial + total_debitos - total_creditos


def buscar_asiento_coincidente(mov_bancario, cuenta_contable):
    """
    Busca un asiento contable que corresponda al movimiento bancario.
    Un "crédito" en el extracto (abono/depósito) incrementa el saldo de la
    cuenta —cuenta de activo— y por tanto corresponde a un "débito" en libros;
    un "débito" del extracto (cargo/retiro) corresponde a un "crédito" en libros.

    Criterios de match (en orden de prioridad):
    1. Mismo valor + misma fecha del asiento
    2. Mismo valor + fecha del asiento dentro de ±3 días
    3. Misma referencia/descripción parcial
    """
    from apps.contabilidad.models import MovimientoContable

    campo_valor = 'debito' if mov_bancario.tipo == 'credito' else 'credito'
    candidatos = MovimientoContable.objects.filter(
        cuenta=cuenta_contable,
        **{campo_valor: mov_bancario.valor},
    ).exclude(
        asiento__movimientos_bancarios__isnull=False,
    ).select_related('asiento')

    match = candidatos.filter(asiento__fecha=mov_bancario.fecha).first()
    if match:
        return match.asiento

    desde = mov_bancario.fecha - datetime.timedelta(days=3)
    hasta = mov_bancario.fecha + datetime.timedelta(days=3)
    match = candidatos.filter(asiento__fecha__range=(desde, hasta)).first()
    if match:
        return match.asiento

    if mov_bancario.referencia:
        match = candidatos.filter(asiento__descripcion__icontains=mov_bancario.referencia).first()
        if match:
            return match.asiento

    for palabra in mov_bancario.descripcion.split():
        if len(palabra) <= 4:
            continue
        match = candidatos.filter(asiento__descripcion__icontains=palabra).first()
        if match:
            return match.asiento

    return None


def conciliar_automatico(extracto):
    """
    Intenta conciliar movimientos del extracto con asientos contables.
    Retorna la cantidad de movimientos conciliados.
    """
    cuenta_contable = extracto.cuenta.cuenta_contable
    conciliados = 0
    for mov_bancario in extracto.movimientos.filter(conciliado=False):
        asiento = buscar_asiento_coincidente(mov_bancario, cuenta_contable)
        if asiento:
            mov_bancario.asiento_contable = asiento
            mov_bancario.conciliado = True
            mov_bancario.save(update_fields=['asiento_contable', 'conciliado'])
            conciliados += 1
    return conciliados


def _items_y_total(partidas, tipo):
    items = [
        {'descripcion': p.descripcion, 'fecha': p.fecha.isoformat(), 'valor': p.valor}
        for p in partidas if p.tipo == tipo
    ]
    total = sum((p.valor for p in partidas if p.tipo == tipo), Decimal('0'))
    return items, total


def generar_reporte_conciliacion(conciliacion):
    extracto = conciliacion.extracto
    cuenta = conciliacion.cuenta
    partidas = list(conciliacion.partidas.all())
    partidas_extracto = [p for p in partidas if p.afecta == 'extracto']
    partidas_libros = [p for p in partidas if p.afecta == 'libros']

    ajustes_al_extracto = {}
    total_ajuste_extracto = Decimal('0')
    for tipo, clave_items, clave_total in BUCKETS_EXTRACTO:
        items, total = _items_y_total(partidas_extracto, tipo)
        ajustes_al_extracto[clave_items] = items
        ajustes_al_extracto[clave_total] = total
        total_ajuste_extracto += total

    ajustes_a_libros = {}
    total_ajuste_libros = Decimal('0')
    for tipo, clave_items, clave_total in BUCKETS_LIBROS:
        items, total = _items_y_total(partidas_libros, tipo)
        ajustes_a_libros[clave_items] = items
        ajustes_a_libros[clave_total] = total
        total_ajuste_libros += total

    saldo_extracto_ajustado = (conciliacion.saldo_extracto + total_ajuste_extracto).quantize(Decimal('0.01'))
    saldo_libros_ajustado = (conciliacion.saldo_libros + total_ajuste_libros).quantize(Decimal('0.01'))
    diferencia_final = (saldo_extracto_ajustado - saldo_libros_ajustado).quantize(Decimal('0.01'))

    movimientos = extracto.movimientos.all()
    total_movimientos = movimientos.count()
    conciliados = movimientos.filter(conciliado=True).count()

    return {
        'cuenta': f"{cuenta.nombre} - {cuenta.numero_cuenta}",
        'periodo': f"{MESES_ES[conciliacion.periodo.month - 1]} {conciliacion.periodo.year}",
        'fecha_reporte': datetime.date.today().isoformat(),

        'saldo_extracto_bancario': conciliacion.saldo_extracto,
        'ajustes_al_extracto': ajustes_al_extracto,
        'saldo_extracto_ajustado': saldo_extracto_ajustado,

        'saldo_en_libros': conciliacion.saldo_libros,
        'ajustes_a_libros': ajustes_a_libros,
        'saldo_libros_ajustado': saldo_libros_ajustado,

        'diferencia_final': diferencia_final,
        'conciliado': diferencia_final == 0,

        'resumen_movimientos': {
            'total_movimientos_extracto': total_movimientos,
            'movimientos_conciliados': conciliados,
            'movimientos_pendientes': total_movimientos - conciliados,
        },
    }

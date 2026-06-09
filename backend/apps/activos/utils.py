"""
Cálculos de depreciación: línea recta, reducción de saldos, suma de dígitos.
"""
from decimal import Decimal, ROUND_HALF_UP
import datetime


def _meses_transcurridos(fecha_inicio: datetime.date, periodo: datetime.date) -> int:
    return (periodo.year - fecha_inicio.year) * 12 + (periodo.month - fecha_inicio.month)


def depreciacion_linea_recta(valor_compra, valor_residual, vida_util_años):
    """Depreciación mensual constante."""
    base = Decimal(str(valor_compra)) - Decimal(str(valor_residual))
    return base / Decimal(vida_util_años * 12)


def depreciacion_reduccion_saldos(valor_compra, valor_residual, valor_en_libros, vida_util_años):
    """Depreciación mensual decreciente (% sobre saldo)."""
    vc = float(valor_compra)
    vr = float(valor_residual)
    if vc <= 0 or vr <= 0:
        return depreciacion_linea_recta(valor_compra, valor_residual, vida_util_años)
    tasa_anual = 1 - (vr / vc) ** (1 / vida_util_años)
    tasa_mensual = Decimal(str(tasa_anual / 12))
    return Decimal(str(valor_en_libros)) * tasa_mensual


def depreciacion_suma_digitos(valor_compra, valor_residual, vida_util_años,
                               fecha_inicio: datetime.date, periodo: datetime.date):
    """Depreciación mensual por suma de dígitos de los años."""
    n = vida_util_años
    suma = Decimal(n * (n + 1)) / 2
    meses = _meses_transcurridos(fecha_inicio, periodo)
    año_actual = min((meses // 12) + 1, n)
    fraccion = Decimal(n - año_actual + 1) / suma
    base = Decimal(str(valor_compra)) - Decimal(str(valor_residual))
    return (base * fraccion) / 12


def calcular_dep_mensual(activo, periodo: datetime.date) -> Decimal:
    """
    Devuelve la depreciación del mes para un activo, respetando:
    - estado activo
    - valor_en_libros no baje del valor_residual
    """
    if activo.estado != 'activo':
        return Decimal('0')

    disponible = Decimal(str(activo.valor_en_libros)) - Decimal(str(activo.valor_residual))
    if disponible <= 0:
        return Decimal('0')

    metodo = activo.metodo_depreciacion
    if metodo == 'linea_recta':
        dep = depreciacion_linea_recta(activo.valor_compra, activo.valor_residual, activo.vida_util_años)
    elif metodo == 'reduccion_saldos':
        dep = depreciacion_reduccion_saldos(
            activo.valor_compra, activo.valor_residual,
            activo.valor_en_libros, activo.vida_util_años
        )
    elif metodo == 'suma_digitos':
        dep = depreciacion_suma_digitos(
            activo.valor_compra, activo.valor_residual,
            activo.vida_util_años, activo.fecha_inicio_depreciacion, periodo
        )
    else:
        dep = depreciacion_linea_recta(activo.valor_compra, activo.valor_residual, activo.vida_util_años)

    dep = min(dep, disponible)
    return dep.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def proyectar_tabla(activo) -> list:
    """Genera la tabla completa de depreciación proyectada (sin modificar la BD)."""
    vida_meses = activo.vida_util_años * 12
    inicio = activo.fecha_inicio_depreciacion
    vl = Decimal(str(activo.valor_compra))
    acum = Decimal('0')
    tabla = []

    for mes in range(1, vida_meses + 1):
        idx = mes - 1
        m = ((inicio.month - 1 + idx) % 12) + 1
        a = inicio.year + (inicio.month - 1 + idx) // 12
        periodo = datetime.date(a, m, 1)

        disponible = vl - Decimal(str(activo.valor_residual))
        if disponible <= Decimal('0'):
            break

        # Simular cálculo con los valores proyectados
        if activo.metodo_depreciacion == 'linea_recta':
            dep = depreciacion_linea_recta(activo.valor_compra, activo.valor_residual, activo.vida_util_años)
        elif activo.metodo_depreciacion == 'reduccion_saldos':
            dep = depreciacion_reduccion_saldos(activo.valor_compra, activo.valor_residual, vl, activo.vida_util_años)
        elif activo.metodo_depreciacion == 'suma_digitos':
            dep = depreciacion_suma_digitos(activo.valor_compra, activo.valor_residual,
                                             activo.vida_util_años, inicio, periodo)
        else:
            dep = depreciacion_linea_recta(activo.valor_compra, activo.valor_residual, activo.vida_util_años)

        dep = min(dep, disponible).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        acum += dep
        vl -= dep

        tabla.append({
            'mes': mes,
            'periodo': periodo.strftime('%Y-%m'),
            'valor_depreciacion': float(dep),
            'depreciacion_acumulada': float(acum),
            'valor_en_libros': float(vl),
        })

    return tabla

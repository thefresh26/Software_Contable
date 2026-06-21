import csv
import datetime
import io
from decimal import Decimal, InvalidOperation

from .models import ExtractoBancario, MovimientoBancario


def _parsear_fecha(valor):
    if isinstance(valor, datetime.datetime):
        return valor.date()
    if isinstance(valor, datetime.date):
        return valor
    return datetime.date.fromisoformat(str(valor).strip()[:10])


def _parsear_decimal(valor):
    if valor in (None, ''):
        return Decimal('0')
    try:
        return Decimal(str(valor).strip().replace(',', ''))
    except InvalidOperation:
        return Decimal('0')


def _leer_filas(archivo):
    """Devuelve un iterable de tuplas (fecha, descripcion, referencia, debitos, creditos, saldo)."""
    nombre = (archivo.name or '').lower()
    if nombre.endswith('.csv'):
        texto = io.TextIOWrapper(archivo.file, encoding='utf-8-sig')
        lector = csv.reader(texto)
        next(lector, None)  # encabezado
        for fila in lector:
            if not any(fila):
                continue
            yield tuple((fila[j] if j < len(fila) else None) for j in range(6))
    else:
        import openpyxl
        wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
        ws = wb.active
        for fila in ws.iter_rows(min_row=2, values_only=True):
            if not any(fila):
                continue
            yield tuple((fila[j] if j < len(fila) else None) for j in range(6))


def importar_extracto(archivo, cuenta, saldo_inicial=Decimal('0')):
    """
    Importa un extracto bancario desde un archivo Excel o CSV.
    Columnas esperadas: fecha | descripcion | referencia | debitos | creditos | saldo
    Retorna (extracto, errores).
    """
    filas = []
    errores = []
    for i, fila in enumerate(_leer_filas(archivo), start=2):
        fecha, descripcion, referencia, debitos, creditos, saldo = fila
        try:
            if not fecha or not descripcion:
                raise ValueError('fecha y descripcion son obligatorios')
            filas.append({
                'fecha': _parsear_fecha(fecha),
                'descripcion': str(descripcion).strip(),
                'referencia': str(referencia or '').strip(),
                'debitos': _parsear_decimal(debitos),
                'creditos': _parsear_decimal(creditos),
                'saldo': _parsear_decimal(saldo),
            })
        except Exception as e:
            errores.append({'fila': i, 'error': str(e)})

    if not filas:
        return None, errores or [{'fila': 0, 'error': 'El archivo no contiene filas válidas'}]

    fechas = [f['fecha'] for f in filas]
    total_debitos = sum((f['debitos'] for f in filas), Decimal('0'))
    total_creditos = sum((f['creditos'] for f in filas), Decimal('0'))

    extracto = ExtractoBancario.objects.create(
        empresa=cuenta.empresa,
        cuenta=cuenta,
        periodo_inicio=min(fechas),
        periodo_fin=max(fechas),
        saldo_inicial_extracto=saldo_inicial,
        saldo_final_extracto=filas[-1]['saldo'],
        total_debitos=total_debitos,
        total_creditos=total_creditos,
        archivo_original=archivo.name,
    )

    for f in filas:
        MovimientoBancario.objects.create(
            extracto=extracto,
            fecha=f['fecha'],
            descripcion=f['descripcion'],
            referencia=f['referencia'],
            tipo='debito' if f['debitos'] > 0 else 'credito',
            valor=f['debitos'] if f['debitos'] > 0 else f['creditos'],
            saldo=f['saldo'],
        )

    return extracto, errores

from django import template

register = template.Library()


@register.filter
def peso(value):
    """Formatea número como peso colombiano: $ 1.234.567"""
    try:
        value = float(value)
        # Formato con separador de miles y sin decimales
        formatted = f"{value:,.0f}".replace(",", ".")
        return f"$ {formatted}"
    except (TypeError, ValueError):
        return "$ 0"


@register.filter
def porcentaje(value):
    """Muestra el valor como porcentaje: 19.00 → 19%"""
    try:
        v = float(value)
        if v == int(v):
            return f"{int(v)}%"
        return f"{v}%"
    except (TypeError, ValueError):
        return "0%"


@register.filter
def tipo_factura_label(tipo):
    labels = {
        'FV': 'FACTURA DE VENTA',
        'FC': 'FACTURA DE COMPRA',
        'NC': 'NOTA CRÉDITO',
        'ND': 'NOTA DÉBITO',
    }
    return labels.get(tipo, tipo)


@register.filter
def estado_badge_class(estado):
    classes = {
        'emitida': 'estado-emitida',
        'borrador': 'estado-borrador',
        'anulada': 'estado-anulada',
        'aprobada': 'estado-aprobada',
        'enviada': 'estado-enviada',
        'rechazada': 'estado-rechazada',
        'vencida': 'estado-vencida',
        'pendiente': 'estado-borrador',
    }
    return classes.get(estado, 'estado-borrador')

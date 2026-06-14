def calcular_digito_verificador(numero: str) -> int:
    """Calcula el dígito verificador de un NIT colombiano."""
    primos = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    suma = sum(int(d) * primos[i] for i, d in enumerate(reversed(numero)))
    residuo = suma % 11
    return residuo if residuo < 2 else 11 - residuo


def validar_nit(nit: str) -> bool:
    """
    Valida el NIT colombiano con dígito verificador.
    Formato esperado: 123456789-1 o 1234567891
    """
    nit_limpio = nit.replace('-', '').replace('.', '').replace(' ', '').strip()
    if len(nit_limpio) < 2 or not nit_limpio.isdigit():
        return False
    numero = nit_limpio[:-1]
    digito_verificador = int(nit_limpio[-1])
    esperado = calcular_digito_verificador(numero)
    return digito_verificador == esperado

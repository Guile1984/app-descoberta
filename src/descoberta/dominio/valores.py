"""Validação dos valores numéricos que entram nos cálculos.

Dinheiro e horas são tratados como `Decimal`, nunca como `float`: com `float`,
0.1 + 0.2 dá 0.30000000000000004, e esse tipo de resíduo apareceria no relatório.
"""

from decimal import Decimal

Numero = int | Decimal

DIAS_UTEIS_POR_MES = 22


def como_decimal(nome: str, valor: Numero) -> Decimal:
    """Converte para `Decimal`, recusando float, valores não finitos e negativos."""
    if isinstance(valor, float):
        raise TypeError(f"{nome}: use int ou Decimal, não float (recebido {valor!r})")
    if isinstance(valor, bool) or not isinstance(valor, int | Decimal):
        raise TypeError(f"{nome} precisa ser um número (recebido {valor!r})")
    decimal = Decimal(valor)
    if not decimal.is_finite():
        raise ValueError(f"{nome} precisa ser um número finito (recebido {valor})")
    if decimal < 0:
        raise ValueError(f"{nome} não pode ser negativo (recebido {valor})")
    return decimal

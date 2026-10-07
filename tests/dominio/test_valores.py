"""Conversão e validação dos valores numéricos que entram nos cálculos."""

from decimal import Decimal

import pytest

from descoberta.dominio.valores import como_decimal


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(0, Decimal(0)), (15, Decimal(15)), (Decimal("99.90"), Decimal("99.90"))],
)
def test_aceita_int_e_decimal(valor, esperado):
    assert como_decimal("custo", valor) == esperado


def test_recusa_float_para_nao_perder_centavos():
    with pytest.raises(TypeError, match="custo"):
        como_decimal("custo", 0.1)


@pytest.mark.parametrize("valor", [True, "10", None])
def test_recusa_tipos_que_nao_sao_numero(valor):
    with pytest.raises(TypeError, match="custo"):
        como_decimal("custo", valor)


@pytest.mark.parametrize("valor", [-1, Decimal("-0.01")])
def test_recusa_negativo(valor):
    with pytest.raises(ValueError, match="custo não pode ser negativo"):
        como_decimal("custo", valor)


@pytest.mark.parametrize("valor", [Decimal("NaN"), Decimal("Infinity")])
def test_recusa_valor_nao_finito(valor):
    with pytest.raises(ValueError, match="custo"):
        como_decimal("custo", valor)

"""Números digitados e exibidos no formato brasileiro (vírgula decimal, ponto de milhar)."""

from decimal import Decimal

import pytest

from descoberta.web.numeros import ler_decimal, moeda, numero, numero_campo


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("20000", Decimal("20000")),
        ("20.000", Decimal("20000")),
        ("1.234.567,89", Decimal("1234567.89")),
        ("7,5", Decimal("7.5")),
        ("3.000,50", Decimal("3000.50")),
        ("0,015", Decimal("0.015")),
        ("  4 ", Decimal("4")),
        ("R$ 400", Decimal("400")),
        ("R$400,00", Decimal("400.00")),
    ],
)
def test_le_numeros_no_formato_brasileiro(texto, esperado):
    valor = ler_decimal("Investimento", texto)
    assert valor == esperado
    assert isinstance(valor, Decimal)


@pytest.mark.parametrize("texto", ["", "   "])
def test_campo_vazio_vira_sem_valor(texto):
    assert ler_decimal("Investimento", texto) is None


def test_ponto_como_decimal_e_recusado_para_nao_virar_outro_numero():
    # "7.5" poderia ser lido como 75: melhor recusar e pedir a vírgula.
    with pytest.raises(ValueError, match="vírgula"):
        ler_decimal("Horas por ocorrência", "7.5")


@pytest.mark.parametrize("texto", ["abc", "1,2,3", "-5", "1.23.4", "12,", ",5", "1e3"])
def test_texto_que_nao_e_numero_e_recusado(texto):
    with pytest.raises(ValueError, match="Custo da hora"):
        ler_decimal("Custo da hora", texto)


@pytest.mark.parametrize(
    ("valor", "texto"),
    [
        (Decimal("20000"), "R$ 20.000,00"),
        (Decimal("6000"), "R$ 6.000,00"),
        (Decimal("0.5"), "R$ 0,50"),
        (Decimal("1234567.891"), "R$ 1.234.567,89"),
    ],
)
def test_moeda(valor, texto):
    assert moeda(valor) == texto


@pytest.mark.parametrize(
    ("valor", "casas", "texto"),
    [
        (Decimal("20000") / Decimal("2600"), 1, "7,7"),
        (Decimal("60"), 1, "60"),
        (Decimal("13.00"), 1, "13"),
        (Decimal("1500.25"), 2, "1.500,25"),
        (Decimal("0.05"), 1, "0,1"),
    ],
)
def test_numero(valor, casas, texto):
    assert numero(valor, casas) == texto


@pytest.mark.parametrize(
    "valor", [Decimal("20000.00"), Decimal("0.015"), Decimal("4"), Decimal("1234567.89")]
)
def test_valor_do_campo_volta_igual_ao_ser_lido(valor):
    # O que aparece no campo, se for salvo de novo sem mexer, precisa dar o mesmo número.
    assert ler_decimal("x", numero_campo(valor)) == valor


def test_valor_do_campo_sem_zeros_inuteis():
    assert numero_campo(Decimal("20000.00")) == "20.000"
    assert numero_campo(Decimal("0.0150")) == "0,015"
    assert numero_campo(None) == ""

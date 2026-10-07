"""Economia mensal e payback (blocos 1, 6 e 9)."""

from decimal import Decimal

import pytest

from descoberta.dominio.payback import economia_mes, payback_dificil_de_aprovar, payback_meses


def test_economia_e_horas_economizadas_vezes_custo_da_hora():
    assert economia_mes(horas_economizadas_mes=30, custo_hora=100) == 3000


def test_economia_soma_outros_ganhos():
    assert economia_mes(30, 100, outros_ganhos_mes=Decimal("500.50")) == Decimal("3500.50")


def test_economia_negativa_e_recusada():
    with pytest.raises(ValueError, match="outros_ganhos_mes"):
        economia_mes(30, 100, outros_ganhos_mes=-1)


def test_exemplo_do_modelo_de_descoberta():
    # R$ 15.000 / (R$ 4.000 − R$ 500) ≈ 4,3 meses
    meses = payback_meses(investimento=15000, economia_mes=4000, operacao_mes=500)
    assert round(meses, 1) == Decimal("4.3")


def test_sem_investimento_o_payback_e_imediato():
    assert payback_meses(0, 3000, 400) == 0


@pytest.mark.parametrize("operacao", [3000, 3500])
def test_sem_ganho_liquido_nao_ha_payback(operacao):
    assert payback_meses(investimento=20000, economia_mes=3000, operacao_mes=operacao) is None


def test_investimento_negativo_e_recusado():
    with pytest.raises(ValueError, match="investimento"):
        payback_meses(-1, 3000, 400)


@pytest.mark.parametrize(
    ("meses", "dificil"),
    [(Decimal("7.7"), False), (Decimal(12), False), (Decimal("12.1"), True), (None, True)],
)
def test_payback_acima_de_12_meses_e_dificil_de_aprovar(meses, dificil):
    assert payback_dificil_de_aprovar(meses) is dificil

"""Contas da proposta: cronograma em semanas, investimento total e validade."""

from datetime import date
from decimal import Decimal

import pytest

from descoberta.dominio.proposta import Periodo, cronograma, investimento_total, valida_ate


def test_fases_em_sequencia_a_partir_do_aceite():
    assert cronograma([4, 8]) == [Periodo(1, 4), Periodo(5, 12)]


def test_uma_semana():
    assert cronograma([1, 1, 2]) == [Periodo(1, 1), Periodo(2, 2), Periodo(3, 4)]


def test_fase_sem_duracao_deixa_as_seguintes_sem_datas():
    assert cronograma([4, None, 3]) == [Periodo(1, 4), None, None]


def test_sem_fases():
    assert cronograma([]) == []


@pytest.mark.parametrize("duracao", [0, -1])
def test_duracao_invalida(duracao):
    with pytest.raises(ValueError, match="duração"):
        cronograma([duracao])


def test_periodo_em_texto():
    assert str(Periodo(1, 4)) == "semanas 1 a 4"
    assert str(Periodo(5, 5)) == "semana 5"


def test_investimento_total():
    assert investimento_total([Decimal("6000"), Decimal("20000")]) == Decimal("26000")


def test_total_com_fase_sem_valor_nao_existe():
    assert investimento_total([Decimal("6000"), None]) is None
    assert investimento_total([]) is None


def test_validade_conta_dias_corridos():
    assert valida_ate(date(2026, 10, 11), 15) == date(2026, 10, 26)
    assert valida_ate(date(2026, 12, 20), 15) == date(2027, 1, 4)

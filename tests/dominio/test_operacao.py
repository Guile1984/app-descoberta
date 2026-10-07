"""Custo mensal de operação (bloco 6)."""

from decimal import Decimal

import pytest

from descoberta.dominio.operacao import custo_operacao_mes


def test_so_custo_fixo():
    assert custo_operacao_mes(custo_fixo_mes=400) == 400


def test_chamadas_usam_22_dias_uteis():
    # 200 chamadas/dia × R$ 0,05 × 22 dias = R$ 220
    assert custo_operacao_mes(chamadas_por_dia=200, custo_por_chamada=Decimal("0.05")) == 220


def test_chamadas_mais_custo_fixo():
    total = custo_operacao_mes(
        chamadas_por_dia=200, custo_por_chamada=Decimal("0.05"), custo_fixo_mes=150
    )
    assert total == Decimal("370")


def test_sem_nada_informado_custa_zero():
    assert custo_operacao_mes() == 0


def test_valor_negativo_e_recusado():
    with pytest.raises(ValueError, match="custo_fixo_mes"):
        custo_operacao_mes(custo_fixo_mes=-1)

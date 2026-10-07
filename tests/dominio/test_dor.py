"""Custo da dor (bloco 1)."""

from decimal import Decimal

import pytest

from descoberta.dominio.dor import custo_dor_mes, horas_dor_mes, ocorrencias_por_mes


def test_ocorrencias_por_mes_ja_mensais():
    assert ocorrencias_por_mes(15, "mes") == 15


def test_ocorrencias_por_dia_usam_22_dias_uteis():
    assert ocorrencias_por_mes(2, "dia") == 44


def test_ocorrencias_por_semana_usam_52_semanas_em_12_meses():
    # 3 por semana × 52 semanas = 156 por ano = 13 por mês
    assert ocorrencias_por_mes(3, "semana") == 13


def test_periodo_desconhecido_gera_erro():
    with pytest.raises(ValueError, match="'ano'"):
        ocorrencias_por_mes(1, "ano")


def test_horas_da_dor_por_mes():
    assert horas_dor_mes(horas_por_ocorrencia=4, ocorrencias_mes=15) == 60


def test_horas_fracionadas():
    assert horas_dor_mes(Decimal("0.5"), 10) == 5


def test_custo_da_dor_por_mes():
    assert custo_dor_mes(horas_mes=60, custo_hora=100) == Decimal(6000)


def test_custo_com_centavos_sem_erro_de_arredondamento():
    assert custo_dor_mes(Decimal("3"), Decimal("33.33")) == Decimal("99.99")


@pytest.mark.parametrize(
    "chamada",
    [
        lambda: ocorrencias_por_mes(-1, "mes"),
        lambda: horas_dor_mes(-4, 15),
        lambda: custo_dor_mes(60, -100),
    ],
)
def test_valores_negativos_sao_recusados(chamada):
    with pytest.raises(ValueError, match="negativ"):
        chamada()

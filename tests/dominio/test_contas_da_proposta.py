"""Contas da proposta: cronograma em semanas, investimento total e validade."""

from datetime import date
from decimal import Decimal

import pytest

from descoberta.dominio.proposta import (
    ItemRepetido,
    Periodo,
    cronograma,
    diferenca_do_investimento,
    investimento_total,
    itens_repetidos,
    valida_ate,
)


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


# --- Avisos: itens repetidos entre fases e total diferente do investimento da métrica ---

FASE_0 = (
    "Fase 0",
    [
        "Diagnóstico das fontes de dados e definição do padrão de coleta",
        "Organização e rotulagem do histórico com o critério do especialista do cliente",
    ],
)


def test_mesmo_item_em_duas_fases():
    fases = [("Fase 0", ["Treinamento da equipe"]), ("MVP", ["  treinamento da EQUIPE. "])]
    assert itens_repetidos(fases) == [
        ItemRepetido("Fase 0", "Treinamento da equipe", "MVP", "  treinamento da EQUIPE. ")
    ]


def test_item_parecido_em_outra_fase():
    """O caso do demo antes do ajuste: a rotulagem das fotos estava no MVP."""
    mvp = ("MVP", ["Organização e rotulagem das cerca de 500 fotos com o critério do Marcos"])
    [repetido] = itens_repetidos([FASE_0, mvp])
    assert repetido.fase == "Fase 0"
    assert repetido.item.startswith("Organização e rotulagem do histórico")
    assert repetido.outra_fase == "MVP"


def test_itens_diferentes_nao_avisam():
    mvp = (
        "MVP",
        [
            "Triagem por foto (grave ou simples), com revisão do Marcos em todos os casos",
            "Envio e devolução pelo WhatsApp ou por upload (integração nível 0 ou 1)",
        ],
    )
    assert itens_repetidos([FASE_0, mvp]) == []


def test_repetido_na_mesma_fase_nao_avisa():
    assert itens_repetidos([("MVP", ["Triagem", "Triagem"])]) == []


def test_tres_fases():
    fases = [("A", ["Rotular fotos"]), ("B", ["Triagem"]), ("C", ["rotular fotos"])]
    assert [(r.fase, r.outra_fase) for r in itens_repetidos(fases)] == [("A", "C")]


def test_diferenca_do_investimento():
    assert diferenca_do_investimento(Decimal("26000"), Decimal("20000")) == Decimal("6000")
    assert diferenca_do_investimento(Decimal("15000"), Decimal("20000")) == Decimal("-5000")


@pytest.mark.parametrize(
    ("total", "investimento"),
    [
        (Decimal("20000"), Decimal("20000.00")),  # igual: sem aviso
        (None, Decimal("20000")),  # fase sem valor: ainda não há total
        (Decimal("20000"), None),  # sessão sem investimento: nada a comparar
    ],
)
def test_sem_diferenca_do_investimento(total, investimento):
    assert diferenca_do_investimento(total, investimento) is None

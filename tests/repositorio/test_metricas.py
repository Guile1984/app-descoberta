"""Métricas numéricas da sessão e notas dos critérios dos scores."""

from decimal import Decimal

import pytest
from sqlmodel import select

from descoberta.repositorio import (
    NotaCriterio,
    RegistroNaoEncontrado,
    notas_da_sessao,
    obter_metricas,
    salvar_metricas,
    salvar_nota,
)

# --- Métricas ---


def test_sem_metricas_devolve_none(session, sessao):
    assert obter_metricas(session, sessao.id) is None


def test_salvar_todas_as_metricas(session, sessao):
    salvar_metricas(
        session,
        sessao.id,
        horas_por_ocorrencia=4,
        frequencia_quantidade=15,
        frequencia_periodo="mes",
        custo_hora=Decimal("100.00"),
        horas_economizadas_mes=30,
        outros_ganhos_mes=Decimal("0"),
        investimento=Decimal("20000.00"),
        chamadas_por_dia=Decimal("120"),
        custo_por_chamada=Decimal("0.015"),
        custo_fixo_mes=Decimal("400.00"),
    )
    session.expire_all()
    m = obter_metricas(session, sessao.id)
    assert m.horas_por_ocorrencia == Decimal(4)
    assert isinstance(m.horas_por_ocorrencia, Decimal)  # int vira Decimal
    assert m.frequencia_quantidade == 15
    assert m.frequencia_periodo == "mes"
    assert m.custo_hora == Decimal("100.00")
    assert m.horas_economizadas_mes == 30
    assert m.outros_ganhos_mes == 0
    assert m.investimento == Decimal("20000.00")
    assert m.chamadas_por_dia == 120
    assert m.custo_por_chamada == Decimal("0.015")
    assert m.custo_fixo_mes == Decimal("400.00")


def test_atualizacao_parcial_preserva_os_outros_campos(session, sessao):
    salvar_metricas(session, sessao.id, custo_hora=100, investimento=20_000)
    salvar_metricas(session, sessao.id, investimento=25_000)
    m = obter_metricas(session, sessao.id)
    assert m.custo_hora == 100
    assert m.investimento == 25_000


def test_none_apaga_um_campo(session, sessao):
    salvar_metricas(session, sessao.id, custo_hora=100)
    salvar_metricas(session, sessao.id, custo_hora=None)
    assert obter_metricas(session, sessao.id).custo_hora is None


@pytest.mark.parametrize(
    ("campos", "excecao", "erro"),
    [
        ({"custo_hora": 100.0}, TypeError, "custo_hora.*float"),
        ({"investimento": -1}, ValueError, "investimento"),
        ({"custo_fixo_mes": Decimal("NaN")}, ValueError, "custo_fixo_mes"),
        ({"custo_hora": "100"}, TypeError, "custo_hora"),
        ({"frequencia_periodo": "ano"}, ValueError, "frequencia_periodo"),
        ({"lucro": 10}, ValueError, "campo desconhecido 'lucro'"),
    ],
)
def test_valores_invalidos(session, sessao, campos, excecao, erro):
    with pytest.raises(excecao, match=erro):
        salvar_metricas(session, sessao.id, **campos)


def test_valor_invalido_nao_grava_os_outros(session, sessao):
    with pytest.raises(TypeError):
        salvar_metricas(session, sessao.id, investimento=20_000, custo_hora=100.0)
    assert obter_metricas(session, sessao.id) is None


def test_metricas_em_sessao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado, match="sessão 999"):
        salvar_metricas(session, 999, custo_hora=100)


# --- Notas dos critérios ---


def test_salvar_notas(session, sessao):
    salvar_nota(session, sessao.id, "volume", 1)
    salvar_nota(session, sessao.id, "dor_clara", 3)
    assert notas_da_sessao(session, sessao.id) == {"volume": 1, "dor_clara": 3}


def test_nota_atualizada_nao_duplica(session, sessao):
    salvar_nota(session, sessao.id, "volume", 1)
    salvar_nota(session, sessao.id, "volume", 2)
    assert notas_da_sessao(session, sessao.id) == {"volume": 2}
    assert len(session.exec(select(NotaCriterio)).all()) == 1


def test_nota_none_apaga(session, sessao):
    salvar_nota(session, sessao.id, "volume", 1)
    salvar_nota(session, sessao.id, "volume", None)
    assert notas_da_sessao(session, sessao.id) == {}


@pytest.mark.parametrize(
    ("nota", "excecao"),
    [(4, ValueError), (-1, ValueError), (Decimal(2), TypeError), (True, TypeError)],
)
def test_nota_invalida(session, sessao, nota, excecao):
    with pytest.raises(excecao, match="nota"):
        salvar_nota(session, sessao.id, "volume", nota)


def test_criterio_invalido(session, sessao):
    with pytest.raises(ValueError, match="criterio_id"):
        salvar_nota(session, sessao.id, "Volume", 1)

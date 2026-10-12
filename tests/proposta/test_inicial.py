"""Conteúdo inicial da proposta: o padrão do modelo mais as saídas da revisão (cópia)."""

from decimal import Decimal
from pathlib import Path

import pytest

from descoberta.proposta import carregar_modelo_proposta
from descoberta.proposta.inicial import DadosDaSessao, conteudo_inicial

MODELO = carregar_modelo_proposta(
    Path(__file__).resolve().parents[2] / "config" / "proposta_v1.yaml"
)

ROBERTO = DadosDaSessao(
    faixa_score_final="seguir_fase_0",
    investimento=Decimal("20000"),
    escopo_entra=["Triagem por foto", "Envio pelo WhatsApp"],
    escopo_fora=["Laudo automático"],
    hipoteses=["Custo da hora: R$ 100,00"],
    passos_do_cliente=["Enviar a amostra com os 40 casos graves"],
)


def test_fases_com_escopo_e_investimento_da_sessao():
    inicial = conteudo_inicial(MODELO.padrao, ROBERTO)
    fase_0, mvp = inicial.fases
    assert fase_0.nome == "Fase 0 — preparação dos dados"
    assert fase_0.duracao_semanas == 4
    assert fase_0.investimento is None  # o preço da fase 0 é do consultor
    assert len(fase_0.escopo) == 3
    assert mvp.escopo == ["Triagem por foto", "Envio pelo WhatsApp"]
    assert mvp.investimento == Decimal("20000")
    assert "MVP funcionando no piloto assistido" in mvp.entregaveis


def test_exclusoes_premissas_e_responsabilidades():
    inicial = conteudo_inicial(MODELO.padrao, ROBERTO)
    assert inicial.exclusoes == ["Laudo automático"]
    assert inicial.premissas[-1] == (
        "Custo da hora: R$ 100,00 (hipótese do consultor, a confirmar com o cliente)"
    )
    assert inicial.premissas[:2] == list(MODELO.padrao.premissas)
    assert inicial.responsabilidades[-1] == "Enviar a amostra com os 40 casos graves"
    assert inicial.responsabilidades[:4] == list(MODELO.padrao.responsabilidades)


def test_condicoes_vem_do_modelo():
    inicial = conteudo_inicial(MODELO.padrao, ROBERTO)
    assert inicial.validade_dias == 15
    assert inicial.condicoes_pagamento.startswith("50% no aceite")
    assert "IPCA" in inicial.reajuste
    assert "tributos" in inicial.impostos


@pytest.mark.parametrize(
    ("faixa", "fases"),
    [
        ("seguir", ["MVP"]),  # dados prontos: sem fase 0
        ("seguir_fase_0", ["Fase 0 — preparação dos dados", "MVP"]),
        ("nao_seguir", ["Fase 0 — preparação dos dados", "MVP"]),
        (None, ["Fase 0 — preparação dos dados", "MVP"]),  # score incompleto: todas
    ],
)
def test_fases_conforme_o_score_final(faixa, fases):
    dados = DadosDaSessao(faixa_score_final=faixa)
    assert [f.nome for f in conteudo_inicial(MODELO.padrao, dados).fases] == fases


def test_sessao_sem_revisao():
    inicial = conteudo_inicial(MODELO.padrao, DadosDaSessao(faixa_score_final=None))
    assert inicial.fases[1].escopo == []
    assert inicial.fases[1].investimento is None
    assert inicial.exclusoes == []

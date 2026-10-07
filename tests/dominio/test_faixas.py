"""Escolha da faixa de um score a partir das faixas do YAML."""

import pytest

from descoberta.dominio.faixas import classificar


@pytest.mark.parametrize(
    ("pontuacao", "faixa"),
    [(0, "fase_0"), (5, "fase_0"), (6, "mvp_ressalvas"), (10, "mvp_ressalvas"), (11, "pronto")],
)
def test_classifica_nas_bordas_das_faixas_de_dados(questionario_v1, pontuacao, faixa):
    faixas = questionario_v1.scores.prontidao_dados.faixas
    assert classificar(pontuacao, faixas).id == faixa


@pytest.mark.parametrize("pontuacao", [-1, 16])
def test_pontuacao_sem_faixa_gera_erro(questionario_v1, pontuacao):
    with pytest.raises(ValueError, match=f"pontuação {pontuacao}"):
        classificar(pontuacao, questionario_v1.scores.prontidao_dados.faixas)

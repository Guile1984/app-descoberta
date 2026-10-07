"""Score de prontidão de dados (bloco 4) e score final de viabilidade (bloco 10)."""

import pytest

from descoberta.dominio.scores import (
    nota_prontidao_para_viabilidade,
    score_prontidao,
    score_viabilidade,
)

CRITERIOS_DADOS = ["disponibilidade", "volume", "rotulos", "qualidade", "acesso_legal"]
CRITERIOS_FINAIS = [
    "dor_clara",
    "ia_caminho_certo",
    "prontidao_dados",
    "retorno_viavel",
    "riscos_controlaveis",
    "comprometimento_cliente",
]


def notas(criterios: list[str], *valores: int) -> dict[str, int]:
    return dict(zip(criterios, valores, strict=True))


def test_score_de_prontidao_soma_as_notas(questionario_v1):
    resultado = score_prontidao(notas(CRITERIOS_DADOS, 3, 2, 1, 2, 3), questionario_v1)
    assert resultado.pontuacao == 11
    assert resultado.maximo == 15
    assert resultado.faixa.id == "pronto"


@pytest.mark.parametrize(
    ("valores", "faixa"),
    [((1, 1, 1, 1, 1), "fase_0"), ((2, 1, 1, 1, 1), "mvp_ressalvas"), ((0,) * 5, "fase_0")],
)
def test_faixas_do_score_de_prontidao(questionario_v1, valores, faixa):
    assert score_prontidao(notas(CRITERIOS_DADOS, *valores), questionario_v1).faixa.id == faixa


@pytest.mark.parametrize(
    ("score", "nota"),
    [(0, 0), (2, 0), (3, 1), (4, 1), (5, 1), (6, 2), (10, 2), (11, 3), (15, 3)],
)
def test_conversao_do_score_de_dados_para_nota_final(questionario_v1, score, nota):
    assert nota_prontidao_para_viabilidade(score, questionario_v1) == nota


@pytest.mark.parametrize("score", [-1, 16])
def test_conversao_fora_da_escala_gera_erro(questionario_v1, score):
    with pytest.raises(ValueError, match=str(score)):
        nota_prontidao_para_viabilidade(score, questionario_v1)


@pytest.mark.parametrize(
    ("valores", "faixa"),
    [
        ((2, 2, 1, 1, 1, 1), "nao_seguir"),  # 8
        ((2, 2, 2, 1, 1, 1), "seguir_fase_0"),  # 9
        ((3, 3, 2, 2, 2, 1), "seguir_fase_0"),  # 13
        ((3, 3, 2, 2, 2, 2), "seguir"),  # 14
        ((3,) * 6, "seguir"),  # 18
    ],
)
def test_faixas_do_score_final(questionario_v1, valores, faixa):
    resultado = score_viabilidade(notas(CRITERIOS_FINAIS, *valores), questionario_v1)
    assert resultado.pontuacao == sum(valores)
    assert resultado.maximo == 18
    assert resultado.faixa.id == faixa


@pytest.mark.parametrize("nota", [-1, 4])
def test_nota_fora_de_0_a_3_e_recusada(questionario_v1, nota):
    with pytest.raises(ValueError, match="volume"):
        score_prontidao(notas(CRITERIOS_DADOS, 1, nota, 1, 1, 1), questionario_v1)


@pytest.mark.parametrize("nota", [True, 1.5, "2"])
def test_nota_precisa_ser_inteira(questionario_v1, nota):
    with pytest.raises(TypeError, match="volume"):
        score_prontidao(notas(CRITERIOS_DADOS, 1, nota, 1, 1, 1), questionario_v1)


def test_criterio_faltando_e_recusado(questionario_v1):
    incompletas = notas(CRITERIOS_DADOS, 1, 1, 1, 1, 1)
    del incompletas["acesso_legal"]
    with pytest.raises(ValueError, match="faltando.*acesso_legal"):
        score_prontidao(incompletas, questionario_v1)


def test_criterio_desconhecido_e_recusado(questionario_v1):
    com_extra = notas(CRITERIOS_FINAIS, 1, 1, 1, 1, 1, 1) | {"prazo": 2}
    with pytest.raises(ValueError, match="desconhecido.*prazo"):
        score_viabilidade(com_extra, questionario_v1)

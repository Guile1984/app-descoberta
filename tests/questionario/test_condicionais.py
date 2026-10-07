"""Resolução das perguntas condicionais pelo tipo de solução (bloco 3)."""

import pytest

from descoberta.questionario import pergunta_visivel, perguntas_visiveis

IDS_VISAO_COMPUTACIONAL = ["b4.vc1", "b4.vc2", "b4.vc3", "b4.vc4"]


def ids(perguntas) -> list[str]:
    return [pergunta.id for pergunta in perguntas]


def test_visao_computacional_abre_as_4_perguntas_do_bloco_4(questionario_v1):
    visiveis = ids(perguntas_visiveis(questionario_v1, 4, "visao_computacional"))
    assert visiveis[-4:] == IDS_VISAO_COMPUTACIONAL
    assert len(visiveis) == len(questionario_v1.bloco(4).perguntas)


@pytest.mark.parametrize("tipo", ["automacao_sem_ia", "ml_classico", "llm_rag", None])
def test_outros_tipos_nao_mostram_perguntas_de_visao(questionario_v1, tipo):
    visiveis = ids(perguntas_visiveis(questionario_v1, 4, tipo))
    assert not set(visiveis) & set(IDS_VISAO_COMPUTACIONAL)
    assert len(visiveis) == 10  # 5 obrigatórias + 5 de aprofundamento


def test_ordem_do_yaml_e_preservada(questionario_v1):
    todas = ids(questionario_v1.bloco(4).perguntas)
    visiveis = ids(perguntas_visiveis(questionario_v1, 4, "visao_computacional"))
    assert visiveis == todas


def test_blocos_sem_condicionais_nao_mudam_com_o_tipo(questionario_v1):
    tipos = [tipo.id for tipo in questionario_v1.tipos_solucao] + [None]
    for bloco in questionario_v1.blocos:
        if bloco.numero == 4:
            continue
        for tipo in tipos:
            assert perguntas_visiveis(questionario_v1, bloco.numero, tipo) == bloco.perguntas


def test_tipo_de_solucao_inexistente_gera_erro(questionario_v1):
    with pytest.raises(ValueError, match="visao"):
        perguntas_visiveis(questionario_v1, 4, "visao")


def test_bloco_inexistente_gera_erro(questionario_v1):
    with pytest.raises(KeyError):
        perguntas_visiveis(questionario_v1, 11, None)


# --- Busca de uma pergunta pelo id (usada pela tela para conferir o que chega) ---


def test_pergunta_encontrada_pelo_id_com_o_seu_bloco(questionario_v1):
    bloco, pergunta = questionario_v1.pergunta("b4.vc2")
    assert bloco.numero == 4
    assert pergunta.id == "b4.vc2"


def test_pergunta_inexistente_gera_erro(questionario_v1):
    with pytest.raises(KeyError, match="b4.o99"):
        questionario_v1.pergunta("b4.o99")


@pytest.mark.parametrize(
    ("pergunta_id", "tipo", "visivel"),
    [
        ("b1.o1", None, True),
        ("b4.vc1", "visao_computacional", True),
        ("b4.vc1", "llm_rag", False),
        ("b4.vc1", None, False),
    ],
)
def test_pergunta_visivel(questionario_v1, pergunta_id, tipo, visivel):
    assert pergunta_visivel(questionario_v1, pergunta_id, tipo) is visivel


def test_pergunta_visivel_com_tipo_inexistente_gera_erro(questionario_v1):
    with pytest.raises(ValueError, match="visao"):
        pergunta_visivel(questionario_v1, "b1.o1", "visao")

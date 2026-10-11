"""Seção `revisao` do questionário: categorias de risco e textos do relatório."""

import pytest
from pydantic import ValidationError

from descoberta.questionario import Questionario


def erro_de(dados: dict) -> str:
    with pytest.raises(ValidationError) as excinfo:
        Questionario.model_validate(dados)
    return str(excinfo.value)


def test_revisao_minima_e_valida(dados_minimos):
    questionario = Questionario.model_validate(dados_minimos)
    assert [c.id for c in questionario.revisao.categorias_risco] == ["lgpd", "outro"]
    [texto] = questionario.revisao.textos
    assert texto.apoio == ["b1.o1", "enc.resumo"]


def test_revisao_e_obrigatoria(dados_minimos):
    del dados_minimos["revisao"]
    assert "revisao" in erro_de(dados_minimos)


def test_apoio_e_opcional(dados_minimos):
    del dados_minimos["revisao"]["textos"][0]["apoio"]
    assert Questionario.model_validate(dados_minimos).revisao.textos[0].apoio == []


def test_categoria_e_texto_por_id(dados_minimos):
    questionario = Questionario.model_validate(dados_minimos)
    assert questionario.categoria_risco("lgpd").rotulo == "LGPD"
    assert questionario.texto_revisao("frase_problema").titulo == "Frase-problema"
    with pytest.raises(KeyError):
        questionario.categoria_risco("inexistente")
    with pytest.raises(KeyError):
        questionario.texto_revisao("inexistente")


@pytest.mark.parametrize("campo", ["categorias_risco", "textos"])
def test_listas_vazias_sao_recusadas(dados_minimos, campo):
    dados_minimos["revisao"][campo] = []
    erro_de(dados_minimos)


def test_categoria_duplicada(dados_minimos):
    dados_minimos["revisao"]["categorias_risco"].append({"id": "lgpd", "rotulo": "De novo"})
    assert "id duplicado 'lgpd'" in erro_de(dados_minimos)


def test_texto_com_id_de_outra_parte_do_questionario(dados_minimos):
    dados_minimos["revisao"]["textos"][0]["id"] = "dor_clara"  # já é um critério
    assert "id duplicado 'dor_clara'" in erro_de(dados_minimos)


def test_apoio_precisa_existir(dados_minimos):
    dados_minimos["revisao"]["textos"][0]["apoio"] = ["b1.o1", "b9.o9"]
    mensagem = erro_de(dados_minimos)
    assert "texto 'frase_problema'" in mensagem
    assert "'b9.o9'" in mensagem


def test_apoio_aceita_perguntas_e_itens_do_encerramento(dados_minimos):
    dados_minimos["revisao"]["textos"][0]["apoio"] = ["b4.vc1", "enc.resumo"]
    Questionario.model_validate(dados_minimos)


# --- Questionário v1 ---

CATEGORIAS_V1 = [
    "lgpd",
    "vies",
    "explicabilidade",
    "responsabilidade_tecnica",
    "seguranca",
    "dependencia_fornecedor",
    "outro",
]

TEXTOS_V1 = [
    "resumo_executivo",
    "frase_problema",
    "fluxo_as_is",
    "fluxo_to_be",
    "justificativa_solucao",
    "recomendacao",
]


def test_v1_categorias_sao_as_linhas_da_tabela_do_bloco_7_mais_outro(questionario_v1):
    categorias = questionario_v1.revisao.categorias_risco
    assert [c.id for c in categorias] == CATEGORIAS_V1
    [tabela] = [r for r in questionario_v1.bloco(7).referencias if r.titulo == "Principais riscos"]
    assert [c.rotulo for c in categorias[:-1]] == [linha[0] for linha in tabela.linhas]
    assert categorias[-1].rotulo == "Outro"


def test_v1_textos_narrativos_do_relatorio(questionario_v1):
    textos = questionario_v1.revisao.textos
    assert [t.id for t in textos] == TEXTOS_V1
    assert all(t.orientacao for t in textos)
    assert questionario_v1.texto_revisao("recomendacao").apoio == ["enc.recomendacao"]


# --- Seções do relatório (bloco 10) ---


def test_secoes_do_relatorio_tem_id_e_titulo(dados_minimos):
    dados_minimos["blocos"][3]["secoes_relatorio"] = [
        {"id": "rel.resumo", "titulo": "Resumo executivo"}
    ]
    [secao] = Questionario.model_validate(dados_minimos).bloco(4).secoes_relatorio
    assert (secao.id, secao.titulo) == ("rel.resumo", "Resumo executivo")


def test_secao_do_relatorio_so_com_texto_e_recusada(dados_minimos):
    dados_minimos["blocos"][3]["secoes_relatorio"] = ["Resumo executivo"]
    erro_de(dados_minimos)


def test_secao_do_relatorio_com_id_repetido(dados_minimos):
    dados_minimos["blocos"][3]["secoes_relatorio"] = [
        {"id": "rel.resumo", "titulo": "Resumo"},
        {"id": "rel.resumo", "titulo": "Outro"},
    ]
    assert "id duplicado 'rel.resumo'" in erro_de(dados_minimos)


def test_secao_traz_respostas_de_blocos_e_tabelas_de_referencia(dados_minimos):
    dados_minimos["blocos"][3]["referencias"] = [
        {"titulo": "Critério de aceite", "colunas": ["Fase"], "linhas": [["1. Teste"]]}
    ]
    dados_minimos["blocos"][3]["secoes_relatorio"] = [
        {
            "id": "rel.dados",
            "titulo": "Dados (bloco 4)",
            "blocos": [4],
            "respostas": ["enc.resumo"],
            "tabelas": ["Critério de aceite"],
        }
    ]
    [secao] = Questionario.model_validate(dados_minimos).bloco(4).secoes_relatorio
    assert secao.blocos == [4]
    assert secao.respostas == ["enc.resumo"]
    assert secao.tabelas == ["Critério de aceite"]
    assert secao.titulo_para_cliente == "Dados"  # sem a referência interna ao bloco


@pytest.mark.parametrize(
    ("campo", "valor", "mensagem"),
    [
        ("blocos", [9], "bloco 9 inexistente"),
        ("respostas", ["b9.o9"], "'b9.o9'"),
        ("tabelas", ["Tabela que não existe"], "'Tabela que não existe'"),
    ],
)
def test_secao_cita_o_que_nao_existe(dados_minimos, campo, valor, mensagem):
    secao = {"id": "rel.dados", "titulo": "Dados", "blocos": [4], campo: valor}
    dados_minimos["blocos"][3]["secoes_relatorio"] = [secao]
    texto = erro_de(dados_minimos)
    assert "seção 'rel.dados'" in texto
    assert mensagem in texto

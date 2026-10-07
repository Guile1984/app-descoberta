"""Fidelidade do config/questionario_v1.yaml ao docs/modelo-descoberta.md."""

import pytest

TITULOS_DOS_BLOCOS = [
    "Problema de negócio",
    "Processo atual × futuro",
    "Adequação de IA",
    "Dados",
    "Critérios de sucesso",
    "Requisitos não funcionais",
    "Riscos e compliance",
    "Integração e infraestrutura",
    "Restrições do projeto",
    "Relatório de Descoberta",
]

# (bloco, obrigatórias sem condição, aprofundamento, sinais de alerta), conforme o modelo.
CONTAGENS_POR_BLOCO = [
    (1, 7, 4, 4),
    (2, 5, 3, 3),
    (3, 5, 3, 3),
    (4, 5, 5, 4),
    (5, 5, 3, 3),
    (6, 6, 4, 3),
    (7, 5, 4, 3),
    (8, 5, 4, 4),
    (9, 5, 4, 4),
    (10, 0, 0, 0),
]


def sem_condicao(perguntas, tipo: str) -> list:
    return [p for p in perguntas if p.tipo == tipo and p.condicao is None]


def todas_as_perguntas(questionario) -> list:
    return [pergunta for bloco in questionario.blocos for pergunta in bloco.perguntas]


def test_versao_e_titulo(questionario_v1):
    assert questionario_v1.versao == 1
    assert questionario_v1.titulo == "Modelo de Descoberta — Apps de IA para PMEs"


def test_dez_blocos_com_titulos_do_modelo(questionario_v1):
    assert [bloco.numero for bloco in questionario_v1.blocos] == list(range(1, 11))
    assert [bloco.titulo for bloco in questionario_v1.blocos] == TITULOS_DOS_BLOCOS


@pytest.mark.parametrize(
    ("numero", "obrigatorias", "aprofundamento", "sinais"), CONTAGENS_POR_BLOCO
)
def test_contagens_por_bloco(questionario_v1, numero, obrigatorias, aprofundamento, sinais):
    bloco = questionario_v1.bloco(numero)
    assert len(sem_condicao(bloco.perguntas, "obrigatoria")) == obrigatorias
    assert len(sem_condicao(bloco.perguntas, "aprofundamento")) == aprofundamento
    assert len(bloco.sinais) == sinais


def test_totais(questionario_v1):
    perguntas = todas_as_perguntas(questionario_v1)
    sinais = [sinal for bloco in questionario_v1.blocos for sinal in bloco.sinais]
    assert len(sem_condicao(perguntas, "obrigatoria")) == 48
    assert len(sem_condicao(perguntas, "aprofundamento")) == 34
    assert len(sinais) == 31


def test_numeracao_das_obrigatorias_segue_o_modelo(questionario_v1):
    for bloco in questionario_v1.blocos:
        obrigatorias = sem_condicao(bloco.perguntas, "obrigatoria")
        esperado = [f"b{bloco.numero}.o{n}" for n in range(1, len(obrigatorias) + 1)]
        assert [p.id for p in obrigatorias] == esperado


def test_textos_de_referencia(questionario_v1):
    textos = {p.id: p.texto for p in todas_as_perguntas(questionario_v1)}
    assert textos["b1.o1"] == "Qual tarefa ou situação mais toma tempo ou dinheiro da empresa hoje?"
    assert textos["b4.vc3"] == (
        "As fotos têm referência de escala (régua, fissurômetro, objeto conhecido)?"
    )
    assert textos["b9.o1"] == "Quanto a empresa pode investir para desenvolver a solução?"


def test_tipos_de_solucao_da_arvore_de_decisao(questionario_v1):
    assert [tipo.id for tipo in questionario_v1.tipos_solucao] == [
        "automacao_sem_ia",
        "ml_classico",
        "llm_rag",
        "visao_computacional",
        "agente_llm",
        "coletar_dados",
    ]


def test_condicionais_sao_as_4_de_visao_computacional_no_bloco_4(questionario_v1):
    condicionais = [p for p in todas_as_perguntas(questionario_v1) if p.condicao]
    assert [p.id for p in condicionais] == ["b4.vc1", "b4.vc2", "b4.vc3", "b4.vc4"]
    assert all(p.condicao.tipos_solucao == ["visao_computacional"] for p in condicionais)
    assert all(p.tipo == "obrigatoria" for p in condicionais)


def test_31_sinais_de_alerta(questionario_v1):
    assert sum(len(bloco.sinais) for bloco in questionario_v1.blocos) == 31


def test_encerramento_com_5_itens(questionario_v1):
    assert [item.titulo for item in questionario_v1.encerramento.itens] == [
        "Resumo",
        "Recomendação preliminar",
        "Próximos passos",
        "Participantes",
        "Prazo",
    ]


def test_bloco_10_tem_as_12_secoes_do_relatorio(questionario_v1):
    bloco = questionario_v1.bloco(10)
    assert len(bloco.secoes_relatorio) == 12
    assert bloco.secoes_relatorio[0].startswith("Resumo executivo")
    assert bloco.secoes_relatorio[-1] == "Recomendação e próximos passos"


def test_score_de_prontidao_de_dados(questionario_v1):
    score = questionario_v1.scores.prontidao_dados
    assert [c.id for c in score.criterios] == [
        "disponibilidade",
        "volume",
        "rotulos",
        "qualidade",
        "acesso_legal",
    ]
    assert score.pontuacao_maxima == 15
    assert [(f.min, f.max, f.id) for f in score.faixas] == [
        (0, 5, "fase_0"),
        (6, 10, "mvp_ressalvas"),
        (11, 15, "pronto"),
    ]
    assert [(f.min, f.max, f.nota) for f in score.conversao_para_nota] == [
        (0, 2, 0),
        (3, 5, 1),
        (6, 10, 2),
        (11, 15, 3),
    ]


def test_score_final_de_viabilidade(questionario_v1):
    score = questionario_v1.scores.viabilidade_final
    assert [(c.id, c.blocos_origem) for c in score.criterios] == [
        ("dor_clara", [1]),
        ("ia_caminho_certo", [3]),
        ("prontidao_dados", [4]),
        ("retorno_viavel", [6, 9]),
        ("riscos_controlaveis", [7]),
        ("comprometimento_cliente", [9]),
    ]
    assert score.pontuacao_maxima == 18
    assert [(f.min, f.max, f.id) for f in score.faixas] == [
        (0, 8, "nao_seguir"),
        (9, 13, "seguir_fase_0"),
        (14, 18, "seguir"),
    ]

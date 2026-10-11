"""Revisão pós-sessão: matriz de riscos 3×3 e o que ainda falta preencher."""

from dataclasses import dataclass
from datetime import date

import pytest

from descoberta.dominio.revisao import (
    Camada,
    Nivel,
    Responsavel,
    matriz_de_riscos,
    pendencias_da_revisao,
    severidade,
)


@dataclass
class Risco:
    descricao: str
    probabilidade: Nivel
    impacto: Nivel
    mitigacao: str | None = "Mitigação definida"


@dataclass
class Indicador:
    nome: str
    camada: Camada
    valor_atual: str | None = "60 h/mês"
    meta: str | None = "30 h/mês"
    prazo: str | None = "3 meses"
    como_medir: str | None = "Planilha de chamados"


@dataclass
class ItemEscopo:
    texto: str
    entra: bool


@dataclass
class ProximoPasso:
    acao: str
    responsavel: Responsavel
    prazo: date | None = date(2026, 10, 9)


B, M, A = Nivel.baixo, Nivel.medio, Nivel.alto

# --- Matriz ---


@pytest.mark.parametrize(
    ("probabilidade", "impacto", "esperada"),
    [
        (B, B, B),
        (B, M, B),
        (M, B, B),
        (B, A, M),
        (M, M, M),
        (A, B, M),
        (M, A, A),
        (A, M, A),
        (A, A, A),
    ],
)
def test_severidade_de_cada_celula(probabilidade, impacto, esperada):
    assert severidade(probabilidade, impacto) == esperada


def test_matriz_vazia_tem_9_celulas_sem_riscos():
    matriz = matriz_de_riscos([])
    assert len(matriz) == 3
    assert all(len(linha) == 3 for linha in matriz)
    assert all(celula.riscos == [] for linha in matriz for celula in linha)


def test_linhas_do_impacto_alto_para_o_baixo_e_colunas_da_probabilidade_baixa_para_a_alta():
    matriz = matriz_de_riscos([])
    assert [linha[0].impacto for linha in matriz] == [A, M, B]
    assert [celula.probabilidade for celula in matriz[0]] == [B, M, A]
    assert matriz[0][2].severidade == A  # canto de cima à direita: alto × alto
    assert matriz[2][0].severidade == B


def test_riscos_numerados_na_ordem_e_colocados_na_celula_certa():
    riscos = [
        Risco("Vazamento de fotos", probabilidade=A, impacto=A),
        Risco("API muda de preço", probabilidade=M, impacto=M),
        Risco("Laudo errado", probabilidade=M, impacto=A),
        Risco("Outro vazamento", probabilidade=A, impacto=A),
    ]
    matriz = matriz_de_riscos(riscos)
    alto_alto = matriz[0][2]
    assert [(n, r.descricao) for n, r in alto_alto.riscos] == [
        (1, "Vazamento de fotos"),
        (4, "Outro vazamento"),
    ]
    assert [n for n, _ in matriz[1][1].riscos] == [2]  # médio × médio
    assert [n for n, _ in matriz[0][1].riscos] == [3]  # impacto alto, probabilidade média


def test_niveis_aceitam_o_texto_gravado():
    [risco] = [
        n for linha in matriz_de_riscos([Risco("x", "alto", "baixo")]) for n in linha if n.riscos
    ]
    assert (risco.probabilidade, risco.impacto) == (A, B)


# --- Pendências ---

TEXTOS = ["resumo_executivo", "frase_problema"]


def completa(**alteracoes):
    """Revisão sem nenhuma pendência; cada teste troca só a parte que interessa."""
    dados = {
        "ids_textos": TEXTOS,
        "textos": {"resumo_executivo": "Resumo.", "frase_problema": "Hoje o Marcos…"},
        "riscos": [Risco("Vazamento", A, A)],
        "indicadores": [Indicador("Horas do Marcos", Camada.negocio)],
        "itens_escopo": [ItemEscopo("Triagem", True), ItemEscopo("Laudo automático", False)],
        "proximos_passos": [ProximoPasso("Enviar amostra", Responsavel.cliente)],
    }
    return pendencias_da_revisao(**(dados | alteracoes))


def test_revisao_completa_nao_tem_pendencias():
    pendencias = completa()
    assert pendencias.total == 0
    assert pendencias.textos == []
    assert pendencias.riscos == pendencias.indicadores == []
    assert pendencias.escopo == pendencias.proximos_passos == []


def test_tudo_vazio():
    pendencias = pendencias_da_revisao(TEXTOS, {}, [], [], [], [])
    assert pendencias.textos == TEXTOS
    assert pendencias.riscos == ["nenhum risco cadastrado"]
    assert pendencias.indicadores == ["nenhum indicador de negócio"]
    assert pendencias.escopo == [
        "nenhum item que entra no MVP",
        "nenhum item que fica fora do MVP",
    ]
    assert pendencias.proximos_passos == ["nenhum próximo passo"]
    assert pendencias.total == 2 + 1 + 1 + 2 + 1


def test_texto_so_com_espacos_conta_como_vazio():
    pendencias = completa(textos={"resumo_executivo": "  \n ", "frase_problema": "Ok"})
    assert pendencias.textos == ["resumo_executivo"]


def test_risco_alto_nos_dois_eixos_exige_mitigacao():
    riscos = [Risco("Vazamento", A, A, mitigacao=None), Risco("Atraso", M, A, mitigacao=None)]
    assert completa(riscos=riscos).riscos == [
        "“Vazamento”: probabilidade e impacto altos exigem mitigação antes do início"
    ]


def test_mitigacao_so_com_espacos_nao_vale():
    assert len(completa(riscos=[Risco("Vazamento", A, A, mitigacao="  ")]).riscos) == 1


def test_indicador_tecnico_sozinho_nao_basta():
    pendencias = completa(indicadores=[Indicador("Recall", Camada.tecnica)])
    assert pendencias.indicadores == ["nenhum indicador de negócio"]


def test_indicador_precisa_das_quatro_colunas_da_tabela_do_bloco_5():
    indicador = Indicador("Horas do Marcos", "negocio", meta=None, como_medir=" ")
    assert completa(indicadores=[indicador]).indicadores == [
        "“Horas do Marcos”: falta meta e como medir"
    ]


def test_indicador_sem_nada():
    indicador = Indicador("Prazo", Camada.negocio, None, None, None, None)
    assert completa(indicadores=[indicador]).indicadores == [
        "“Prazo”: falta valor atual, meta, prazo e como medir"
    ]


def test_escopo_so_com_o_que_entra():
    pendencias = completa(itens_escopo=[ItemEscopo("Triagem", True)])
    assert pendencias.escopo == ["nenhum item que fica fora do MVP"]


def test_proximo_passo_sem_prazo():
    passos = [ProximoPasso("Enviar amostra", Responsavel.cliente, prazo=None)]
    assert completa(proximos_passos=passos).proximos_passos == ["“Enviar amostra”: sem prazo"]

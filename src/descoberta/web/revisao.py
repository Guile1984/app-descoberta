"""Revisão pós-sessão: as quatro listas da tela e tudo o que a página mostra.

As listas (riscos, indicadores, escopo e próximos passos) usam as rotas e os templates
genéricos de `web/listas.py`; aqui fica o que é próprio de cada uma (`Lista`).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session

from descoberta.campos import CAMPO_POR_NOME, CampoNumerico
from descoberta.dominio.pendencias import obrigatorias_pendentes
from descoberta.dominio.revisao import matriz_de_riscos, pendencias_da_revisao
from descoberta.formatos import moeda, numero
from descoberta.questionario import Questionario
from descoberta.repositorio import (
    CAMPOS_NUMERICOS,
    Indicador,
    ItemEscopo,
    ProximoPasso,
    Risco,
    Sessao,
    hipoteses_da_sessao,
    itens_da_sessao,
    obter_metricas,
    respostas_da_sessao,
    textos_da_sessao,
)
from descoberta.rotulos import CAMADAS, ESCOPO, IMPACTOS, PROBABILIDADES, RESPONSAVEIS

from .formularios import data_iso
from .listas import Formulario, Lista

# Os mesmos rótulos para todos os templates da revisão.
ROTULOS = {
    "probabilidades": PROBABILIDADES,
    "impactos": IMPACTOS,
    "camadas": CAMADAS,
    "responsaveis": RESPONSAVEIS,
    "opcoes_escopo": ESCOPO,
}


def _escolha(formulario: Formulario, campo: str, rotulo: str) -> str:
    """Valor de um <select> com a opção "Escolha…" (vazia) no topo."""
    valor = formulario.get(campo, "")
    if not valor:
        raise ValueError(f"escolha {rotulo}")
    return valor


def _risco(questionario: Questionario, formulario: Formulario) -> dict[str, Any]:
    categoria = _escolha(formulario, "categoria", "a categoria")
    try:
        questionario.categoria_risco(categoria)
    except KeyError:
        raise ValueError(f"a categoria '{categoria}' não existe no questionário") from None
    return {
        "descricao": formulario.get("descricao", ""),
        "categoria": categoria,
        "probabilidade": _escolha(formulario, "probabilidade", "a probabilidade"),
        "impacto": _escolha(formulario, "impacto", "o impacto"),
        "mitigacao": formulario.get("mitigacao", ""),
    }


def _indicador(_questionario: Questionario, formulario: Formulario) -> dict[str, Any]:
    campos = ("nome", "camada", "valor_atual", "meta", "prazo", "como_medir")
    return {campo: formulario.get(campo, "") for campo in campos}


def _item_escopo(_questionario: Questionario, formulario: Formulario) -> dict[str, Any]:
    entra = formulario.get("entra", "")
    if entra not in ESCOPO:
        raise ValueError("diga se o item entra no MVP ou fica de fora")
    return {"texto": formulario.get("texto", ""), "entra": entra == "sim"}


def _proximo_passo(_questionario: Questionario, formulario: Formulario) -> dict[str, Any]:
    prazo = formulario.get("prazo", "").strip()
    return {
        "acao": formulario.get("acao", ""),
        "responsavel": formulario.get("responsavel", ""),
        "prazo": data_iso("data do prazo", prazo) if prazo else None,
    }


LISTAS = {
    lista.nome: lista
    for lista in (
        Lista(
            "riscos",
            "Matriz de riscos",
            "Riscos altos em probabilidade e impacto exigem mitigação antes do início.",
            "risco",
            Risco,
            ("descricao", "categoria", "probabilidade", "impacto", "mitigacao"),
            _risco,
        ),
        Lista(
            "indicadores",
            "Indicadores de sucesso",
            "Indicador atual → meta → prazo → como medir, nas camadas de negócio e técnica.",
            "indicador",
            Indicador,
            ("nome", "camada", "valor_atual", "meta", "prazo", "como_medir"),
            _indicador,
        ),
        Lista(
            "escopo",
            "Escopo do MVP",
            "O que entra e o que fica de fora do MVP.",
            "item",
            ItemEscopo,
            ("texto", "entra"),
            _item_escopo,
        ),
        Lista(
            "passos",
            "Próximos passos",
            "O que o cliente envia e o que o consultor entrega, com prazo.",
            "passo",
            ProximoPasso,
            ("acao", "responsavel", "prazo"),
            _proximo_passo,
        ),
    )
}


@dataclass(frozen=True)
class GrupoPendencias:
    titulo: str
    ancora: str  # id da seção na página, para o link
    mensagens: list[str]


def _apoio(questionario: Questionario, respostas: Mapping[str, str]) -> dict:
    """Para cada texto: (rótulo, resposta) das perguntas e itens de apoio do YAML."""
    apoio = {}
    for texto in questionario.revisao.textos:
        itens = []
        for id_ in texto.apoio:
            try:
                bloco, pergunta = questionario.pergunta(id_)
                rotulo = f"Bloco {bloco.numero} · {pergunta.texto}"
            except KeyError:
                rotulo = f"Encerramento · {questionario.item_encerramento(id_).titulo}"
            itens.append((rotulo, respostas.get(id_)))
        apoio[texto.id] = itens
    return apoio


def _hipoteses(banco: Session, sessao_id: int) -> list[tuple[CampoNumerico, str, bool]]:
    """Cada métrica numérica: (campo, valor formatado, se está marcada como hipótese)."""
    metricas = obter_metricas(banco, sessao_id)
    marcadas = hipoteses_da_sessao(banco, sessao_id)
    linhas = []
    for nome in CAMPOS_NUMERICOS:
        campo = CAMPO_POR_NOME[nome]
        valor = getattr(metricas, nome) if metricas else None
        if valor is None:
            texto = "—"
        elif campo.unidade == "R$":
            texto = moeda(valor)
        else:
            texto = f"{numero(valor, 2)} {campo.unidade}".strip()
        linhas.append((campo, texto, nome in marcadas))
    return linhas


def contexto_das_listas(
    _banco: Session, _sessao: Sessao, questionario: Questionario
) -> dict[str, Any]:
    """O que os templates das listas da revisão usam (categorias de risco e rótulos)."""
    return {"questionario": questionario, **ROTULOS}


def contexto_da_revisao(banco: Session, sessao: Sessao, questionario: Questionario) -> dict:
    textos = textos_da_sessao(banco, sessao.id)
    itens = {
        nome: itens_da_sessao(banco, lista.modelo, sessao.id) for nome, lista in LISTAS.items()
    }
    respostas = respostas_da_sessao(banco, sessao.id)
    pendencias = pendencias_da_revisao(
        [texto.id for texto in questionario.revisao.textos],
        textos,
        itens["riscos"],
        itens["indicadores"],
        itens["escopo"],
        itens["passos"],
    )
    grupos = [
        GrupoPendencias(
            "Textos do relatório",
            "textos",
            [f"{questionario.texto_revisao(id_).titulo}: em branco" for id_ in pendencias.textos],
        ),
        GrupoPendencias(LISTAS["riscos"].titulo, "lista-riscos", pendencias.riscos),
        GrupoPendencias(LISTAS["indicadores"].titulo, "lista-indicadores", pendencias.indicadores),
        GrupoPendencias(LISTAS["escopo"].titulo, "lista-escopo", pendencias.escopo),
        GrupoPendencias(LISTAS["passos"].titulo, "lista-passos", pendencias.proximos_passos),
    ]
    obrigatorias = obrigatorias_pendentes(questionario, sessao.tipo_solucao, respostas)
    return {
        "sessao": sessao,
        "questionario": questionario,
        "textos": textos,
        "apoio": _apoio(questionario, respostas),
        "listas": LISTAS,
        "itens": itens,
        "matriz": matriz_de_riscos(itens["riscos"]),
        "grupos_pendencias": [grupo for grupo in grupos if grupo.mensagens],
        "total_pendencias": pendencias.total,
        "obrigatorias_sem_resposta": sum(len(ids) for ids in obrigatorias.values()),
        "hipoteses": _hipoteses(banco, sessao.id),
        **ROTULOS,
    }

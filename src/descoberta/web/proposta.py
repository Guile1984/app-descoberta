"""Proposta Comercial na tela: as listas (fases, escopo, entregáveis…) e os campos.

As listas usam as rotas e os templates genéricos de `web/listas.py`. Escopo, entregáveis,
exclusões, premissas e responsabilidades dividem uma tabela (ItemProposta); o filtro de
cada lista (tipo=…) separa os itens.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session

from descoberta.formatos import ler_decimal
from descoberta.proposta import ModeloProposta
from descoberta.proposta.clausulas import Ajuste
from descoberta.questionario import Questionario
from descoberta.repositorio import (
    FaseProposta,
    ItemProposta,
    Sessao,
    TipoItemProposta,
    itens_da_sessao,
)

from .formularios import inteiro_ou_nada
from .listas import Formulario, Lista

EVENTO = "proposta-mudou"
FASES_MUDARAM = "fases-mudaram"


def _fase(_questionario: Questionario, formulario: Formulario) -> dict[str, Any]:
    return {
        "nome": formulario.get("nome", ""),
        "objetivo": formulario.get("objetivo", ""),
        "duracao_semanas": inteiro_ou_nada(
            "Duração (semanas)", formulario.get("duracao_semanas", "")
        ),
        "investimento": ler_decimal("Investimento", formulario.get("investimento", "")),
    }


def _item_de_fase(_questionario: Questionario, formulario: Formulario) -> dict[str, Any]:
    fase = formulario.get("fase_id", "")
    if not fase.isdigit():
        raise ValueError("escolha a fase")
    return {"texto": formulario.get("texto", ""), "fase_id": int(fase)}


def _item_simples(_questionario: Questionario, formulario: Formulario) -> dict[str, Any]:
    return {"texto": formulario.get("texto", "")}


def _lista_de_itens(
    nome: str, titulo: str, explicacao: str, tipo: TipoItemProposta, de_fase: bool
) -> Lista:
    return Lista(
        nome,
        titulo,
        explicacao,
        "item",
        ItemProposta,
        ("texto", "fase_id") if de_fase else ("texto",),
        _item_de_fase if de_fase else _item_simples,
        pagina="proposta",
        molde="item_de_fase" if de_fase else "item_simples",
        filtro=(("tipo", tipo),),
        recarregar_em=FASES_MUDARAM if de_fase else None,
    )


LISTAS = {
    lista.nome: lista
    for lista in (
        Lista(
            "fases",
            "Fases",
            "Feitas uma depois da outra, a partir do aceite. Excluir uma fase exclui junto o "
            "escopo e os entregáveis dela.",
            "fase",
            FaseProposta,
            ("nome", "objetivo", "duracao_semanas", "investimento"),
            _fase,
            pagina="proposta",
            eventos=(FASES_MUDARAM,),
        ),
        _lista_de_itens(
            "escopo", "Escopo por fase", "O que cada fase inclui.", TipoItemProposta.escopo, True
        ),
        _lista_de_itens(
            "entregaveis",
            "Entregáveis",
            "O que o cliente recebe ao fim de cada fase.",
            TipoItemProposta.entregavel,
            True,
        ),
        _lista_de_itens(
            "exclusoes",
            "Fora do escopo",
            "O que não faz parte da proposta (veio dos itens que ficam fora do MVP).",
            TipoItemProposta.exclusao,
            False,
        ),
        _lista_de_itens(
            "premissas",
            "Premissas e hipóteses",
            "Condições para os prazos e valores valerem; as hipóteses vieram da revisão.",
            TipoItemProposta.premissa,
            False,
        ),
        _lista_de_itens(
            "responsabilidades",
            "Responsabilidades do cliente",
            "O que o cliente se compromete a fazer.",
            TipoItemProposta.responsabilidade,
            False,
        ),
    )
}

# Campos da proposta na tela, na ordem: (campo, rótulo, tipo do campo).
CAMPOS_DO_CLIENTE = (
    ("cliente_representante", "Representante (quem assina)", "texto"),
    ("cliente_cargo", "Cargo", "texto"),
    ("cliente_cpf_cnpj", "CPF ou CNPJ do cliente", "texto"),
    ("cliente_email", "E-mail", "texto"),
)
CAMPOS_DAS_CONDICOES = (
    ("condicoes_pagamento", "Condições de pagamento", "longo"),
    ("impostos", "Impostos", "longo"),
    ("reajuste", "Reajuste", "longo"),
    ("validade_dias", "Validade (dias)", "numero"),
)


def converter_campo(campo: str, texto: str) -> Any:
    """Texto do campo → valor do repositório (só a validade é número)."""
    if campo == "validade_dias":
        return inteiro_ou_nada("Validade (dias)", texto)
    return texto


def contexto_das_listas(
    banco: Session, sessao: Sessao, _questionario: Questionario
) -> dict[str, Any]:
    """O que os templates das listas da proposta usam: as fases, para escolher e mostrar."""
    fases = itens_da_sessao(banco, FaseProposta, sessao.id)
    return {"fases": fases, "nome_da_fase": {f.id: f.nome for f in fases}}


@dataclass(frozen=True)
class ClausulaNaTela:
    id: str
    titulo: str
    texto: str  # o texto efetivo, com os marcadores ({foro}…)
    texto_do_modelo: str
    removivel: bool
    ajustada: bool
    excluida: bool


def clausula_na_tela(modelo: ModeloProposta, clausula_id: str, ajuste: Ajuste) -> ClausulaNaTela:
    clausula = modelo.clausula(clausula_id)
    return ClausulaNaTela(
        id=clausula.id,
        titulo=clausula.titulo,
        texto=ajuste.texto if ajuste.texto is not None else clausula.texto,
        texto_do_modelo=clausula.texto,
        removivel=clausula.removivel,
        ajustada=ajuste.texto is not None,
        excluida=ajuste.excluida and clausula.removivel,
    )


def clausulas_na_tela(
    modelo: ModeloProposta, ajustes: Mapping[str, Ajuste]
) -> list[ClausulaNaTela]:
    """Todas as cláusulas do modelo (inclusive as excluídas, para incluir de volta)."""
    return [clausula_na_tela(modelo, c.id, ajustes.get(c.id, Ajuste())) for c in modelo.clausulas]

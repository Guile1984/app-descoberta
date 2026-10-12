"""Proposta Comercial na tela: as listas (fases, escopo, entregáveis…) e os campos.

As listas usam as rotas e os templates genéricos de `web/listas.py`. Escopo, entregáveis,
exclusões, premissas e responsabilidades dividem uma tabela (ItemProposta); o filtro de
cada lista (tipo=…) separa os itens.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlmodel import Session

from descoberta.dominio.proposta import (
    ItemRepetido,
    diferenca_do_investimento,
    investimento_total,
    itens_repetidos,
)
from descoberta.formatos import ler_decimal
from descoberta.proposta import ModeloProposta
from descoberta.proposta.clausulas import Ajuste
from descoberta.questionario import Questionario
from descoberta.repositorio import (
    DestinoRascunho,
    FaseProposta,
    ItemProposta,
    Sessao,
    SituacaoRascunho,
    TipoItemProposta,
    itens_da_sessao,
    rascunhos_da_sessao,
)

from .formularios import inteiro_ou_nada
from .listas import Formulario, Lista
from .llm import Alvo

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
    ("cliente_cidade", "Cidade", "texto"),
    ("cliente_uf", "UF", "uf"),
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


def alvo_da_proposta(sessao_id: int, campo: str) -> Alvo:
    """Onde o rascunho de um texto da proposta aparece: o contexto ou o objetivo de uma fase
    ("objetivo_fase.<id>", dentro do item da fase na lista)."""
    if campo == "contexto":
        return Alvo(
            id_html="rascunho-proposta-contexto",
            url_gerar=f"/sessoes/{sessao_id}/proposta/textos/contexto/rascunho",
            aceitar="#bloco-contexto-proposta",
        )
    fase_id = campo.removeprefix("objetivo_fase.")
    return Alvo(
        id_html=f"rascunho-fase-{fase_id}",
        url_gerar=f"/sessoes/{sessao_id}/proposta/fases/{fase_id}/objetivo/rascunho",
        aceitar=f"#fases-{fase_id}",
    )


def rascunhos_pendentes_da_proposta(banco: Session, sessao_id: int) -> dict:
    """Rascunhos da proposta esperando decisão, por campo."""
    return {
        r.campo: r
        for r in rascunhos_da_sessao(
            banco, sessao_id, destino=DestinoRascunho.proposta, situacao=SituacaoRascunho.pendente
        )
    }


def contexto_das_listas(
    banco: Session, sessao: Sessao, _questionario: Questionario
) -> dict[str, Any]:
    """O que os templates das listas da proposta usam: as fases, para escolher e mostrar, e
    o rascunho do objetivo de cada fase."""
    fases = itens_da_sessao(banco, FaseProposta, sessao.id)
    pendentes = rascunhos_pendentes_da_proposta(banco, sessao.id)
    return {
        "fases": fases,
        "nome_da_fase": {f.id: f.nome for f in fases},
        "rascunhos_fases": {f.id: pendentes.get(f"objetivo_fase.{f.id}") for f in fases},
        "alvos_fases": {f.id: alvo_da_proposta(sessao.id, f"objetivo_fase.{f.id}") for f in fases},
    }


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


# --- Avisos da proposta (só alertam; nada é mudado) ---


@dataclass(frozen=True)
class AvisosDaProposta:
    repetidos: list[ItemRepetido]  # itens de escopo que parecem estar em mais de uma fase
    total: Decimal | None  # soma das fases (None: alguma fase sem valor)
    investimento: Decimal | None  # o da métrica (bloco 9), usado no payback do relatório

    @property
    def diferenca(self) -> Decimal | None:
        return diferenca_do_investimento(self.total, self.investimento)


def avisos(
    fases: Sequence[tuple[str, Sequence[str], Decimal | None]], investimento: Decimal | None
) -> AvisosDaProposta:
    """`fases`: (nome, itens de escopo, investimento) de cada fase, na ordem."""
    return AvisosDaProposta(
        repetidos=itens_repetidos([(nome, escopo) for nome, escopo, _ in fases]),
        total=investimento_total([valor for _, _, valor in fases]),
        investimento=investimento,
    )


def avisos_da_proposta_gravada(
    banco: Session, sessao_id: int, investimento: Decimal | None
) -> AvisosDaProposta:
    escopo = itens_da_sessao(banco, ItemProposta, sessao_id, tipo=TipoItemProposta.escopo)
    fases = [
        (fase.nome, [i.texto for i in escopo if i.fase_id == fase.id], fase.investimento)
        for fase in itens_da_sessao(banco, FaseProposta, sessao_id)
    ]
    return avisos(fases, investimento)

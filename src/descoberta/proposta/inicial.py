"""Conteúdo inicial de uma proposta nova: o padrão do modelo mais as saídas da revisão.

Tudo é copiado: depois de criada, a proposta é editada à parte, e mudar a revisão não a
altera (renegociar a proposta também nunca mexe no relatório).
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal

from .modelos import Padrao

SUFIXO_HIPOTESE = " (hipótese do consultor, a confirmar com o cliente)"


@dataclass(frozen=True)
class DadosDaSessao:
    """O que a proposta nova aproveita da sessão e da revisão."""

    faixa_score_final: str | None  # id da faixa; None: score final incompleto
    investimento: Decimal | None = None
    escopo_entra: list[str] = field(default_factory=list)
    escopo_fora: list[str] = field(default_factory=list)
    hipoteses: list[str] = field(default_factory=list)  # "Custo da hora: R$ 100,00"
    passos_do_cliente: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FaseInicial:
    nome: str
    objetivo: str
    duracao_semanas: int
    investimento: Decimal | None
    escopo: list[str]
    entregaveis: list[str]


@dataclass(frozen=True)
class PropostaInicial:
    validade_dias: int
    condicoes_pagamento: str
    impostos: str
    reajuste: str
    fases: list[FaseInicial]
    exclusoes: list[str]
    premissas: list[str]
    responsabilidades: list[str]


def como_responsabilidade(passo: str, verbos: Mapping[str, str]) -> str:
    """O próximo passo do cliente escrito como responsabilidade.

    Começando por um substantivo da regra do modelo, ganha o verbo ("Reunião com o Marcos…"
    → "Participar da reunião com o Marcos…"); o resto (em geral, já começando por um verbo,
    como "Enviar a amostra…") fica como está. Regra fixa, sem LLM.
    """
    texto = " ".join(passo.split())
    primeira, _, resto = texto.partition(" ")
    chave = primeira.strip(".,;:").lower()
    for substantivo, verbo in verbos.items():
        if chave == substantivo.lower():
            return " ".join(p for p in (verbo, primeira[0].lower() + primeira[1:], resto) if p)
    return texto


def conteudo_inicial(padrao: Padrao, sessao: DadosDaSessao) -> PropostaInicial:
    fases = [
        FaseInicial(
            nome=fase.nome,
            objetivo=fase.objetivo,
            duracao_semanas=fase.duracao_semanas,
            investimento=sessao.investimento if fase.investimento_da_sessao else None,
            escopo=[*fase.escopo, *(sessao.escopo_entra if fase.escopo_da_revisao else [])],
            entregaveis=list(fase.entregaveis),
        )
        for fase in padrao.fases
        # Score incompleto: todas as fases entram, e o consultor tira o que não servir.
        if not fase.faixas_score_final
        or sessao.faixa_score_final is None
        or sessao.faixa_score_final in fase.faixas_score_final
    ]
    return PropostaInicial(
        validade_dias=padrao.validade_dias,
        condicoes_pagamento=padrao.condicoes_pagamento,
        impostos=padrao.impostos,
        reajuste=padrao.reajuste,
        fases=fases,
        exclusoes=list(sessao.escopo_fora),
        premissas=[*padrao.premissas, *(h + SUFIXO_HIPOTESE for h in sessao.hipoteses)],
        responsabilidades=[
            *padrao.responsabilidades,
            *(
                como_responsabilidade(p, padrao.passos_como_responsabilidade)
                for p in sessao.passos_do_cliente
            ),
        ],
    )

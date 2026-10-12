"""Dados da Proposta Comercial, lidos do banco.

- `dados_para_proposta_nova`: o que uma proposta nova copia da sessão e da revisão.
- `coletar_dados_proposta`: tudo o que a montagem do documento usa.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlmodel import Session

from descoberta.campos import CAMPO_POR_NOME, CAMPOS_METRICAS
from descoberta.formatos import moeda, numero
from descoberta.proposta import ModeloProposta
from descoberta.proposta.clausulas import ClausulaEfetiva, clausulas_efetivas
from descoberta.proposta.inicial import DadosDaSessao
from descoberta.questionario import Questionario
from descoberta.repositorio import (
    FaseProposta,
    ItemProposta,
    RegistroNaoEncontrado,
    TipoItemProposta,
    TipoVersao,
    ajustes_das_clausulas,
    itens_da_sessao,
    obter_proposta,
    versoes_da_sessao,
)

from .dados import DadosRelatorio, coletar_dados


def _valor_da_metrica(campo: str, valor: Decimal) -> str:
    unidade = CAMPO_POR_NOME[campo].unidade
    if unidade == "R$":
        return moeda(valor)
    return f"{numero(valor, 2)} {unidade}".strip()


def faixa_do_score_final(dados: DadosRelatorio) -> str | None:
    """Id da faixa do score final (None: score incompleto)."""
    resultado = dados.painel.score_final.resultado
    return resultado.faixa.id if resultado else None


def dados_para_proposta_nova(dados: DadosRelatorio) -> DadosDaSessao:
    """Escopo, exclusões, hipóteses e passos do cliente, como estão agora na revisão."""
    hipoteses = [
        f"{campo.rotulo}: {_valor_da_metrica(campo.nome, getattr(dados.entradas, campo.nome))}"
        for campo in CAMPOS_METRICAS
        if campo.nome in dados.hipoteses and getattr(dados.entradas, campo.nome) is not None
    ]
    return DadosDaSessao(
        faixa_score_final=faixa_do_score_final(dados),
        investimento=dados.entradas.investimento,
        escopo_entra=[i.texto for i in dados.escopo if i.entra],
        escopo_fora=[i.texto for i in dados.escopo if not i.entra],
        hipoteses=hipoteses,
        passos_do_cliente=[p.acao for p in dados.proximos_passos if p.responsavel == "cliente"],
    )


@dataclass(frozen=True)
class FaseDaProposta:
    nome: str
    objetivo: str | None
    duracao_semanas: int | None
    investimento: Decimal | None
    escopo: list[str]
    entregaveis: list[str]


@dataclass(frozen=True)
class RelatorioReferido:
    """Última versão do relatório registrada para o cliente: a proposta se refere a ela."""

    numero: int
    emitido_em: datetime
    hash_conteudo: str


@dataclass(frozen=True)
class DadosProposta:
    relatorio: DadosRelatorio  # cliente, consultor, textos, indicadores e o Painel
    modelo: ModeloProposta
    cliente_cpf_cnpj: str | None
    cliente_representante: str | None
    cliente_cargo: str | None
    cliente_email: str | None
    cliente_cidade: str | None
    cliente_uf: str | None
    condicoes_pagamento: str
    impostos: str
    reajuste: str
    validade_dias: int
    criada_com_alerta: bool
    fases: list[FaseDaProposta]
    exclusoes: list[str]
    premissas: list[str]
    responsabilidades: list[str]
    relatorio_registrado: RelatorioReferido | None
    clausulas: list[ClausulaEfetiva]  # Condições Gerais: o modelo com os ajustes


def coletar_dados_proposta(
    session: Session, sessao_id: int, questionario: Questionario, modelo: ModeloProposta
) -> DadosProposta:
    """Lê a proposta da sessão; RegistroNaoEncontrado se ela ainda não foi criada."""
    relatorio = coletar_dados(session, sessao_id, questionario)
    proposta = obter_proposta(session, sessao_id)
    if proposta is None:
        raise RegistroNaoEncontrado(f"a sessão {sessao_id} não tem proposta")
    itens = itens_da_sessao(session, ItemProposta, sessao_id)

    def textos(tipo: TipoItemProposta, fase_id: int | None = None) -> list[str]:
        return [i.texto for i in itens if i.tipo == tipo and i.fase_id == fase_id]

    fases = [
        FaseDaProposta(
            nome=fase.nome,
            objetivo=fase.objetivo,
            duracao_semanas=fase.duracao_semanas,
            investimento=fase.investimento,
            escopo=textos(TipoItemProposta.escopo, fase.id),
            entregaveis=textos(TipoItemProposta.entregavel, fase.id),
        )
        for fase in itens_da_sessao(session, FaseProposta, sessao_id)
    ]
    registrada = next(
        (v for v in versoes_da_sessao(session, sessao_id) if v.tipo == TipoVersao.cliente), None
    )
    return DadosProposta(
        relatorio=relatorio,
        modelo=modelo,
        cliente_cpf_cnpj=proposta.cliente_cpf_cnpj,
        cliente_representante=proposta.cliente_representante,
        cliente_cargo=proposta.cliente_cargo,
        cliente_email=proposta.cliente_email,
        cliente_cidade=proposta.cliente_cidade,
        cliente_uf=proposta.cliente_uf,
        condicoes_pagamento=proposta.condicoes_pagamento,
        impostos=proposta.impostos,
        reajuste=proposta.reajuste,
        validade_dias=proposta.validade_dias,
        criada_com_alerta=proposta.criada_com_alerta,
        fases=fases,
        exclusoes=textos(TipoItemProposta.exclusao),
        premissas=textos(TipoItemProposta.premissa),
        responsabilidades=textos(TipoItemProposta.responsabilidade),
        relatorio_registrado=(
            RelatorioReferido(registrada.numero, registrada.emitido_em, registrada.hash_conteudo)
            if registrada
            else None
        ),
        clausulas=clausulas_efetivas(modelo, ajustes_das_clausulas(session, sessao_id)),
    )

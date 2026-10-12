"""Tudo o que o relatório usa, lido do banco de uma vez.

Os números vêm do `Painel` do domínio, o mesmo da tela ao vivo: o relatório não faz
nenhuma conta própria (um teste de arquitetura garante isso).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlmodel import Session

from descoberta.dominio.painel import EntradasPainel, Painel, calcular_painel
from descoberta.dominio.revisao import PendenciasRevisao, pendencias_da_revisao
from descoberta.questionario import Questionario
from descoberta.repositorio import (
    Indicador,
    ItemEscopo,
    ProximoPasso,
    RegistroNaoEncontrado,
    Risco,
    anotacoes_da_sessao,
    hipoteses_da_sessao,
    itens_da_sessao,
    notas_da_sessao,
    obter_cliente,
    obter_metricas,
    obter_perfil,
    obter_sessao,
    respostas_da_sessao,
    sinais_marcados,
    textos_da_sessao,
)

from .consultor import Consultor


@dataclass(frozen=True)
class SinalDoRelatorio:
    id: str
    observacao: str | None


@dataclass(frozen=True)
class AnotacaoDoRelatorio:
    bloco: int | None
    texto: str
    criado_em: datetime


@dataclass(frozen=True)
class DadosRelatorio:
    questionario: Questionario
    empresa: str
    cliente: str
    setor: str | None
    data_sessao: date
    tipo_solucao: str | None
    respostas: Mapping[str, str]
    entradas: EntradasPainel
    painel: Painel
    hipoteses: set[str]
    notas: Mapping[str, int]
    textos: Mapping[str, str]
    riscos: list[Any]
    indicadores: list[Any]
    escopo: list[Any]
    proximos_passos: list[Any]
    sinais: list[SinalDoRelatorio]
    anotacoes: list[AnotacaoDoRelatorio]
    pendencias: PendenciasRevisao
    consultor: Consultor | None  # None: perfil ainda não preenchido


def coletar_dados(session: Session, sessao_id: int, questionario: Questionario) -> DadosRelatorio:
    """Lê a sessão inteira. ValueError: dado gravado que o questionário não reconhece."""
    sessao = obter_sessao(session, sessao_id)
    if sessao is None:
        raise RegistroNaoEncontrado(f"sessão {sessao_id} não encontrada")
    cliente = obter_cliente(session, sessao.cliente_id)
    entradas = EntradasPainel.de(obter_metricas(session, sessao_id))
    notas = notas_da_sessao(session, sessao_id)
    marcados = sinais_marcados(session, sessao_id)
    textos = textos_da_sessao(session, sessao_id)
    listas = {
        modelo: itens_da_sessao(session, modelo, sessao_id)
        for modelo in (Risco, Indicador, ItemEscopo, ProximoPasso)
    }
    return DadosRelatorio(
        questionario=questionario,
        empresa=cliente.empresa,
        cliente=cliente.nome,
        setor=cliente.setor,
        data_sessao=sessao.data,
        tipo_solucao=sessao.tipo_solucao,
        respostas=respostas_da_sessao(session, sessao_id),
        entradas=entradas,
        painel=calcular_painel(entradas, notas, [s.sinal_id for s in marcados], questionario),
        hipoteses=hipoteses_da_sessao(session, sessao_id),
        notas=notas,
        textos=textos,
        riscos=listas[Risco],
        indicadores=listas[Indicador],
        escopo=listas[ItemEscopo],
        proximos_passos=listas[ProximoPasso],
        sinais=[SinalDoRelatorio(s.sinal_id, s.observacao) for s in marcados],
        anotacoes=[
            AnotacaoDoRelatorio(a.bloco, a.texto, a.criado_em)
            for a in anotacoes_da_sessao(session, sessao_id)
        ],
        consultor=Consultor.do_perfil(obter_perfil(session)),
        pendencias=pendencias_da_revisao(
            [t.id for t in questionario.revisao.textos],
            textos,
            listas[Risco],
            listas[Indicador],
            listas[ItemEscopo],
            listas[ProximoPasso],
        ),
    )

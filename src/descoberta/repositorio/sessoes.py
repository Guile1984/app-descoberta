"""Sessões de descoberta: uma por reunião com o cliente."""

from datetime import date
from typing import Any

from sqlmodel import Session, col, select

from ._comum import (
    aplicar_campos,
    booleano,
    dia,
    exigir,
    exigir_sessao,
    gravar,
    id_questionario_opcional,
    inteiro,
    opcao,
    texto_opcional,
    validar_campos,
)
from .modelos import Cliente, Sessao, StatusSessao

# A versão do questionário fica de fora de propósito: a sessão continua presa à versão
# com que foi aberta, para as respostas sempre baterem com as perguntas.
_VALIDADORES_ATUALIZACAO = {
    "data": dia,
    "tipo_solucao": id_questionario_opcional,
    "status": opcao(StatusSessao),
    "contexto_previo": texto_opcional,
    "amostra_dados_recebida": booleano,
}


def _versao(nome: str, valor: Any) -> int:
    return inteiro(nome, valor, minimo=1)


def criar_sessao(
    session: Session,
    *,
    cliente_id: int,
    data: date,
    versao_questionario: int,
    tipo_solucao: str | None = None,
    status: StatusSessao | str = StatusSessao.preparacao,
    contexto_previo: str | None = None,
    amostra_dados_recebida: bool = False,
) -> Sessao:
    campos = validar_campos(
        {
            "versao_questionario": versao_questionario,
            "data": data,
            "tipo_solucao": tipo_solucao,
            "status": status,
            "contexto_previo": contexto_previo,
            "amostra_dados_recebida": amostra_dados_recebida,
        },
        _VALIDADORES_ATUALIZACAO | {"versao_questionario": _versao},
    )
    exigir(session, Cliente, cliente_id, "cliente")
    return gravar(session, Sessao(cliente_id=cliente_id, **campos))


def obter_sessao(session: Session, sessao_id: int) -> Sessao | None:
    return session.get(Sessao, sessao_id)


def listar_sessoes(session: Session, cliente_id: int) -> list[Sessao]:
    """Sessões do cliente, da mais recente para a mais antiga."""
    consulta = (
        select(Sessao)
        .where(Sessao.cliente_id == cliente_id)
        .order_by(col(Sessao.data).desc(), col(Sessao.id).desc())
    )
    return list(session.exec(consulta))


def atualizar_sessao(session: Session, sessao_id: int, **campos: Any) -> Sessao:
    sessao = exigir_sessao(session, sessao_id)
    aplicar_campos(sessao, campos, _VALIDADORES_ATUALIZACAO)
    return gravar(session, sessao)


def excluir_sessao(session: Session, sessao_id: int) -> None:
    """Exclui a sessão e, em cascata, respostas, sinais, anotações, métricas e relatórios."""
    session.delete(exigir_sessao(session, sessao_id))
    session.commit()

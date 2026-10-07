"""Cadastro de clientes."""

from typing import Any

from sqlmodel import Session, select

from ._comum import (
    aplicar_campos,
    exigir,
    gravar,
    inteiro_opcional,
    texto_obrigatorio,
    texto_opcional,
    validar_campos,
)
from .modelos import Cliente

_VALIDADORES = {
    "nome": texto_obrigatorio,
    "empresa": texto_obrigatorio,
    "setor": texto_opcional,
    "num_funcionarios": inteiro_opcional,
    "contato": texto_opcional,
}


def criar_cliente(
    session: Session,
    *,
    nome: str,
    empresa: str,
    setor: str | None = None,
    num_funcionarios: int | None = None,
    contato: str | None = None,
) -> Cliente:
    campos = validar_campos(
        {
            "nome": nome,
            "empresa": empresa,
            "setor": setor,
            "num_funcionarios": num_funcionarios,
            "contato": contato,
        },
        _VALIDADORES,
    )
    return gravar(session, Cliente(**campos))


def obter_cliente(session: Session, cliente_id: int) -> Cliente | None:
    return session.get(Cliente, cliente_id)


def listar_clientes(session: Session) -> list[Cliente]:
    return list(session.exec(select(Cliente).order_by(Cliente.empresa, Cliente.nome)))


def atualizar_cliente(session: Session, cliente_id: int, **campos: Any) -> Cliente:
    cliente = exigir(session, Cliente, cliente_id, "cliente")
    aplicar_campos(cliente, campos, _VALIDADORES)
    return gravar(session, cliente)


def excluir_cliente(session: Session, cliente_id: int) -> None:
    """Exclui o cliente e, em cascata, todas as suas sessões e o que pertence a elas."""
    session.delete(exigir(session, Cliente, cliente_id, "cliente"))
    session.commit()

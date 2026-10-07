"""Validação da entrada e utilidades compartilhadas pelas funções do repositório."""

import re
from collections.abc import Callable, Mapping
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlmodel import Session, SQLModel

from descoberta.dominio.valores import Numero, como_decimal
from descoberta.questionario.modelos import NOTA_MAXIMA_POR_CRITERIO, PADRAO_ID

from .modelos import Sessao


class RegistroNaoEncontrado(LookupError):
    """O registro pedido (cliente, sessão, anotação…) não existe no banco."""


def exigir[M: SQLModel](session: Session, modelo: type[M], id_: int, nome: str) -> M:
    registro = session.get(modelo, id_)
    if registro is None:
        raise RegistroNaoEncontrado(f"{nome} {id_} não encontrado(a)")
    return registro


def exigir_sessao(session: Session, sessao_id: int) -> Sessao:
    return exigir(session, Sessao, sessao_id, "sessão")


def gravar[M: SQLModel](session: Session, registro: M) -> M:
    """Grava um registro numa transação própria e devolve-o atualizado (com id)."""
    session.add(registro)
    session.commit()
    session.refresh(registro)
    return registro


Validadores = Mapping[str, Callable[[str, Any], Any]]


def validar_campos(campos: Mapping[str, Any], validadores: Validadores) -> dict[str, Any]:
    """Valida cada campo com o validador do seu nome; campo sem validador é recusado."""
    desconhecidos = [nome for nome in campos if nome not in validadores]
    if desconhecidos:
        raise ValueError(f"campo desconhecido '{desconhecidos[0]}'")
    return {nome: validadores[nome](nome, valor) for nome, valor in campos.items()}


def aplicar_campos(registro: SQLModel, campos: Mapping[str, Any], validadores: Validadores):
    """Valida todos os campos antes de alterar qualquer um, para não gravar pela metade."""
    for nome, valor in validar_campos(campos, validadores).items():
        setattr(registro, nome, valor)


# --- Validadores: recebem o nome do campo (para a mensagem de erro) e o valor. ---


def texto_obrigatorio(nome: str, valor: Any) -> str:
    if not isinstance(valor, str):
        raise TypeError(f"{nome} precisa ser texto (recebido {valor!r})")
    if not valor.strip():
        raise ValueError(f"{nome} não pode ficar vazio")
    return valor.strip()


def texto_opcional(nome: str, valor: Any) -> str | None:
    """Texto aparado; em branco ou None vira None (sem valor)."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise TypeError(f"{nome} precisa ser texto (recebido {valor!r})")
    return valor.strip() or None


def inteiro(nome: str, valor: Any, minimo: int = 0, maximo: int | None = None) -> int:
    # bool é subclasse de int em Python (True == 1); aqui não serve como número.
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nome} precisa ser um número inteiro (recebido {valor!r})")
    if valor < minimo or (maximo is not None and valor > maximo):
        limite = f"entre {minimo} e {maximo}" if maximo is not None else f"no mínimo {minimo}"
        raise ValueError(f"{nome} deve ser {limite} (recebido {valor})")
    return valor


def inteiro_opcional(nome: str, valor: Any, minimo: int = 0) -> int | None:
    return None if valor is None else inteiro(nome, valor, minimo)


def nota(nome: str, valor: Any) -> int:
    return inteiro(nome, valor, 0, NOTA_MAXIMA_POR_CRITERIO)


def booleano(nome: str, valor: Any) -> bool:
    if not isinstance(valor, bool):
        raise TypeError(f"{nome} precisa ser verdadeiro ou falso (recebido {valor!r})")
    return valor


def dia(nome: str, valor: Any) -> date:
    # datetime é subclasse de date; a sessão guarda só o dia.
    if isinstance(valor, datetime) or not isinstance(valor, date):
        raise TypeError(f"{nome} precisa ser uma data (recebido {valor!r})")
    return valor


def id_questionario(nome: str, valor: Any) -> str:
    """Id vindo do YAML: guardado exatamente como está, sem nenhuma transformação."""
    if not isinstance(valor, str) or not re.fullmatch(PADRAO_ID, valor):
        raise ValueError(
            f"{nome} {valor!r} inválido; use o id como está no questionário "
            "(letras minúsculas sem acento, números, '_' e '.')"
        )
    return valor


def id_questionario_opcional(nome: str, valor: Any) -> str | None:
    return None if valor is None else id_questionario(nome, valor)


def decimal_opcional(nome: str, valor: Numero | None) -> Decimal | None:
    # como_decimal (camada dominio) recusa float, negativos e valores não finitos.
    return None if valor is None else como_decimal(nome, valor)


def opcao[E: StrEnum](tipo: type[E]) -> Callable[[str, Any], E]:
    def validar(nome: str, valor: Any) -> E:
        try:
            return tipo(valor)
        except ValueError:
            aceitos = ", ".join(f"'{membro}'" for membro in tipo)
            raise ValueError(f"{nome} {valor!r} inválido; use {aceitos}") from None

    return validar

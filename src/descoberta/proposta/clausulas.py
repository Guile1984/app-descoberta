"""Cláusulas efetivas de uma proposta: as do modelo, com os ajustes daquela proposta.

O modelo (YAML) define as cláusulas padrão. Em cada proposta, o consultor pode trocar o
texto de uma cláusula ou excluir uma cláusula removível, sem mexer no modelo. Ao
registrar uma versão, o texto efetivo fica congelado com ela.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass

from .modelos import MARCADORES, ModeloProposta, marcadores_desconhecidos

_MARCADOR = re.compile(r"\{([^{}]*)\}")


@dataclass(frozen=True)
class Ajuste:
    """O que uma proposta mudou numa cláusula: o texto (None: o do modelo) ou a exclusão."""

    texto: str | None = None
    excluida: bool = False


@dataclass(frozen=True)
class ClausulaEfetiva:
    id: str
    titulo: str
    texto: str  # ainda com os marcadores ({foro}…): a montagem preenche
    removivel: bool
    ajustada: bool  # texto diferente do modelo


def clausulas_efetivas(
    modelo: ModeloProposta, ajustes: Mapping[str, Ajuste]
) -> list[ClausulaEfetiva]:
    """As cláusulas que entram na proposta, na ordem do modelo.

    Ajustes de cláusulas que não existem mais no modelo são ignorados.
    """
    efetivas = []
    for clausula in modelo.clausulas:
        ajuste = ajustes.get(clausula.id, Ajuste())
        if ajuste.excluida and clausula.removivel:
            continue
        efetivas.append(
            ClausulaEfetiva(
                id=clausula.id,
                titulo=clausula.titulo,
                texto=ajuste.texto if ajuste.texto is not None else clausula.texto,
                removivel=clausula.removivel,
                ajustada=ajuste.texto is not None,
            )
        )
    return efetivas


def conferir_ajuste(
    modelo: ModeloProposta,
    clausula_id: str,
    *,
    texto: str | None = None,
    excluida: bool = False,
) -> None:
    """ValueError se o ajuste não vale: excluir cláusula não removível ou marcador errado.

    KeyError se o modelo não tem a cláusula.
    """
    clausula = modelo.clausula(clausula_id)
    if excluida and not clausula.removivel:
        raise ValueError(f"a cláusula '{clausula.titulo}' não pode ser excluída da proposta")
    if texto is not None:
        desconhecidos = marcadores_desconhecidos(texto)
        if desconhecidos:
            aceitos = ", ".join(f"{{{m}}}" for m in MARCADORES)
            raise ValueError(f"marcador desconhecido {{{desconhecidos[0]}}}; use {aceitos}")


def preencher_marcadores(texto: str, valores: Mapping[str, str | None], falta: str) -> str:
    """Troca cada {marcador} pelo valor; sem valor, pela marca do que falta (`falta`)."""
    return _MARCADOR.sub(lambda m: valores.get(m.group(1)) or falta, texto)


__all__ = [
    "Ajuste",
    "ClausulaEfetiva",
    "clausulas_efetivas",
    "conferir_ajuste",
    "marcadores_desconhecidos",
    "preencher_marcadores",
]

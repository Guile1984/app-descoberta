"""Escolha da faixa em que uma pontuação cai.

As faixas vêm do questionário (YAML); nenhum limite de faixa é escrito no código.
"""

from collections.abc import Iterable
from typing import Protocol


class _Intervalo(Protocol):
    @property
    def min(self) -> int: ...

    @property
    def max(self) -> int: ...


def classificar[T: _Intervalo](pontuacao: int, faixas: Iterable[T]) -> T:
    """Devolve a faixa [min, max] que contém a pontuação."""
    faixas = list(faixas)
    for faixa in faixas:
        if faixa.min <= pontuacao <= faixa.max:
            return faixa
    limites = ", ".join(f"{faixa.min}–{faixa.max}" for faixa in faixas)
    raise ValueError(f"pontuação {pontuacao} fora das faixas ({limites})")

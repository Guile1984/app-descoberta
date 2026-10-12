"""Contas da Proposta Comercial: cronograma, investimento total e validade.

O cronograma é em semanas contadas a partir do aceite (e não em datas): a proposta não
sabe quando o cliente vai aceitar. As fases são feitas uma depois da outra.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class Periodo:
    inicio: int  # semana de início (a semana 1 começa no aceite)
    fim: int

    def __str__(self) -> str:
        if self.inicio == self.fim:
            return f"semana {self.inicio}"
        return f"semanas {self.inicio} a {self.fim}"


def cronograma(duracoes: Sequence[int | None]) -> list[Periodo | None]:
    """Período de cada fase, em sequência. Depois de uma fase sem duração, as seguintes
    ficam sem período (None): não dá para saber quando começam."""
    periodos: list[Periodo | None] = []
    proxima = 1
    for duracao in duracoes:
        if duracao is not None and duracao < 1:
            raise ValueError(f"duração de fase inválida: {duracao} semana(s)")
        if duracao is None or proxima is None:
            periodos.append(None)
            proxima = None
            continue
        periodos.append(Periodo(proxima, proxima + duracao - 1))
        proxima += duracao
    return periodos


def investimento_total(valores: Sequence[Decimal | None]) -> Decimal | None:
    """Soma das fases; sem total (None) se alguma fase ainda não tem valor."""
    if not valores or any(valor is None for valor in valores):
        return None
    return sum(valores, Decimal(0))


def valida_ate(emissao: date, dias: int) -> date:
    """Último dia de validade: a emissão mais `dias` dias corridos."""
    return emissao + timedelta(days=dias)

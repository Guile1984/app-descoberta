"""Custo mensal da dor (bloco 1): o teto do orçamento razoável."""

from decimal import Decimal
from typing import Literal

from .valores import DIAS_UTEIS_POR_MES, Numero, como_decimal

Periodo = Literal["dia", "semana", "mes"]

# Fator de conversão para mês, como fração (numerador, denominador). Multiplicar antes de
# dividir mantém a conta exata: 3 por semana × 52 / 12 = 13, e não 12,999…
_FATOR_MENSAL: dict[str, tuple[int, int]] = {
    "dia": (DIAS_UTEIS_POR_MES, 1),
    "semana": (52, 12),
    "mes": (1, 1),
}


def ocorrencias_por_mes(quantidade: Numero, periodo: Periodo) -> Decimal:
    """Converte a frequência informada pelo cliente para ocorrências por mês."""
    if periodo not in _FATOR_MENSAL:
        raise ValueError(f"período {periodo!r} inválido; use 'dia', 'semana' ou 'mes'")
    numerador, denominador = _FATOR_MENSAL[periodo]
    return como_decimal("quantidade", quantidade) * numerador / denominador


def horas_dor_mes(horas_por_ocorrencia: Numero, ocorrencias_mes: Numero) -> Decimal:
    horas = como_decimal("horas_por_ocorrencia", horas_por_ocorrencia)
    return horas * como_decimal("ocorrencias_mes", ocorrencias_mes)


def custo_dor_mes(horas_mes: Numero, custo_hora: Numero) -> Decimal:
    return como_decimal("horas_mes", horas_mes) * como_decimal("custo_hora", custo_hora)

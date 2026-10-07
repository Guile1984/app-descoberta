"""Custo mensal de operação (bloco 6), para comparar com o custo da dor."""

from decimal import Decimal

from .valores import DIAS_UTEIS_POR_MES, Numero, como_decimal


def custo_operacao_mes(
    *,
    chamadas_por_dia: Numero = 0,
    custo_por_chamada: Numero = 0,
    custo_fixo_mes: Numero = 0,
) -> Decimal:
    """Chamadas por dia × custo por chamada × 22 dias úteis + custo fixo (nuvem, licenças)."""
    variavel = (
        como_decimal("chamadas_por_dia", chamadas_por_dia)
        * como_decimal("custo_por_chamada", custo_por_chamada)
        * DIAS_UTEIS_POR_MES
    )
    return variavel + como_decimal("custo_fixo_mes", custo_fixo_mes)

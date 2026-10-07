"""Economia mensal e payback (cruza os blocos 1, 6 e 9)."""

from decimal import Decimal

from .valores import Numero, como_decimal

# Para PMEs, payback acima de 12 meses é difícil de aprovar (Modelo de Descoberta, bloco 9).
LIMITE_PAYBACK_MESES = 12


def economia_mes(
    horas_economizadas_mes: Numero, custo_hora: Numero, outros_ganhos_mes: Numero = 0
) -> Decimal:
    """Horas economizadas × custo da hora + outros ganhos mensais (R$)."""
    horas = como_decimal("horas_economizadas_mes", horas_economizadas_mes)
    custo_hora = como_decimal("custo_hora", custo_hora)
    return horas * custo_hora + como_decimal("outros_ganhos_mes", outros_ganhos_mes)


def payback_meses(
    investimento: Numero, economia_mes: Numero, operacao_mes: Numero
) -> Decimal | None:
    """Investimento / (economia mensal − custo mensal de operação).

    Devolve None quando a economia não supera a operação: o projeto nunca se paga.
    """
    investimento = como_decimal("investimento", investimento)
    economia = como_decimal("economia_mes", economia_mes)
    ganho_liquido = economia - como_decimal("operacao_mes", operacao_mes)
    if ganho_liquido <= 0:
        return None
    return investimento / ganho_liquido


def payback_dificil_de_aprovar(meses: Decimal | None) -> bool:
    return meses is None or meses > LIMITE_PAYBACK_MESES

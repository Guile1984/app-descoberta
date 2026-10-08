"""Campos numéricos da sessão (tabela Metricas) e em que bloco cada um aparece na tela.

Não é o questionário: são os campos do banco que os cálculos usam. O bloco de cada um é
só onde o campo é mostrado, perto das perguntas que levantam aquele número.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CampoNumerico:
    nome: str  # mesmo nome do campo em Metricas e do parâmetro em dominio
    rotulo: str
    bloco: int
    unidade: str = ""  # "R$", "h" ou nada


CAMPOS_METRICAS = (
    # Bloco 1 — custo da dor.
    CampoNumerico("horas_por_ocorrencia", "Horas por ocorrência", 1, "h"),
    CampoNumerico("frequencia_quantidade", "Ocorrências", 1),
    CampoNumerico("frequencia_periodo", "Período da frequência", 1),
    CampoNumerico("custo_hora", "Custo da hora", 1, "R$"),
    # Bloco 6 — custo de operação.
    CampoNumerico("chamadas_por_dia", "Chamadas por dia", 6),
    CampoNumerico("custo_por_chamada", "Custo por chamada", 6, "R$"),
    CampoNumerico("custo_fixo_mes", "Custo fixo mensal", 6, "R$"),
    # Bloco 9 — retorno.
    CampoNumerico("horas_economizadas_mes", "Horas economizadas por mês", 9, "h"),
    CampoNumerico("outros_ganhos_mes", "Outros ganhos mensais", 9, "R$"),
    CampoNumerico("investimento", "Investimento", 9, "R$"),
)

CAMPO_POR_NOME = {campo.nome: campo for campo in CAMPOS_METRICAS}

# Os períodos que o cálculo do custo da dor entende (dominio.dor.Periodo).
PERIODOS = {"dia": "por dia útil", "semana": "por semana", "mes": "por mês"}


def campos_do_bloco(numero: int) -> list[CampoNumerico]:
    return [campo for campo in CAMPOS_METRICAS if campo.bloco == numero]

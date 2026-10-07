"""Carrega e valida o questionário (YAML) e resolve as perguntas condicionais."""

from .carregador import QuestionarioInvalido, carregar_questionario
from .condicionais import pergunta_visivel, perguntas_visiveis
from .modelos import (
    Bloco,
    Faixa,
    FaixaNota,
    Pergunta,
    Questionario,
    Sinal,
    TipoSolucao,
)

__all__ = [
    "Bloco",
    "Faixa",
    "FaixaNota",
    "Pergunta",
    "Questionario",
    "QuestionarioInvalido",
    "Sinal",
    "TipoSolucao",
    "carregar_questionario",
    "pergunta_visivel",
    "perguntas_visiveis",
]

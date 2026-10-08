"""Carrega e valida o questionário (YAML) e resolve as perguntas condicionais."""

from .carregador import QuestionarioInvalido, carregar_questionario
from .condicionais import pergunta_visivel, perguntas_visiveis
from .modelos import (
    Bloco,
    Duracao,
    Faixa,
    FaixaNota,
    ItemEncerramento,
    Pergunta,
    Questionario,
    Sinal,
    TipoSolucao,
)

__all__ = [
    "Bloco",
    "Duracao",
    "Faixa",
    "FaixaNota",
    "ItemEncerramento",
    "Pergunta",
    "Questionario",
    "QuestionarioInvalido",
    "Sinal",
    "TipoSolucao",
    "carregar_questionario",
    "pergunta_visivel",
    "perguntas_visiveis",
]

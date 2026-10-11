"""Carrega e valida o questionário (YAML) e resolve as perguntas condicionais."""

from .carregador import QuestionarioInvalido, carregar_questionario
from .condicionais import pergunta_visivel, perguntas_visiveis
from .modelos import (
    Bloco,
    CategoriaRisco,
    Duracao,
    Faixa,
    FaixaNota,
    ItemEncerramento,
    Pergunta,
    Questionario,
    SecaoRelatorio,
    Sinal,
    TextoRevisao,
    TipoSolucao,
)

__all__ = [
    "Bloco",
    "CategoriaRisco",
    "Duracao",
    "Faixa",
    "FaixaNota",
    "ItemEncerramento",
    "Pergunta",
    "Questionario",
    "QuestionarioInvalido",
    "SecaoRelatorio",
    "Sinal",
    "TextoRevisao",
    "TipoSolucao",
    "carregar_questionario",
    "pergunta_visivel",
    "perguntas_visiveis",
]

"""Modelo da Proposta Comercial: o arquivo YAML editável fora do código.

modelo = carregar_modelo_proposta("config/proposta_v1.yaml")
"""

from pathlib import Path

from descoberta.questionario.carregador import ArquivoInvalido, carregar_yaml

from .modelos import (
    MARCADORES,
    Clausula,
    CriterioDeAceite,
    FasePadrao,
    ModeloProposta,
    Padrao,
    problemas_com_o_questionario,
)


class ModeloPropostaInvalido(ArquivoInvalido):
    """O arquivo do modelo da proposta não pôde ser lido ou não passou na validação."""

    NOME = "Modelo da proposta"


def carregar_modelo_proposta(caminho: Path | str) -> ModeloProposta:
    return carregar_yaml(caminho, ModeloProposta, ModeloPropostaInvalido)


__all__ = [
    "MARCADORES",
    "Clausula",
    "CriterioDeAceite",
    "FasePadrao",
    "ModeloProposta",
    "ModeloPropostaInvalido",
    "Padrao",
    "carregar_modelo_proposta",
    "problemas_com_o_questionario",
]

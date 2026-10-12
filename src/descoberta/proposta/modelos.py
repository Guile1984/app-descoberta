"""Modelos Pydantic do modelo da Proposta Comercial (config/proposta_v*.yaml).

Como o questionário, o modelo vive fora do código e é validado quando a app liga. As
referências ao questionário (faixas do score final, tabela do critério de aceite) são
conferidas por `problemas_com_o_questionario`, porque dependem dos dois arquivos.
"""

import re
from collections import Counter
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from descoberta.questionario import Questionario
from descoberta.questionario.modelos import PADRAO_ID

Id = Annotated[str, StringConstraints(pattern=PADRAO_ID)]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# Marcadores que os textos das cláusulas podem usar: a montagem troca pelo valor.
MARCADORES = {
    "cliente.empresa": "empresa do cliente",
    "consultor.empresa": "empresa do consultor",
    "consultor.nome": "nome do consultor",
    "foro": "cidade/UF do consultor (perfil)",
}
_MARCADOR = re.compile(r"\{([^{}]*)\}")


def marcadores_desconhecidos(texto: str) -> list[str]:
    """Marcadores {…} do texto que a montagem não conhece (lista vazia: tudo certo)."""
    return [nome for nome in _MARCADOR.findall(texto) if nome not in MARCADORES]


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Clausula(_Modelo):
    """Cláusula das Condições Gerais. Removível: pode ser excluída de uma proposta."""

    id: Id
    titulo: Texto
    texto: Texto
    removivel: bool = False

    @field_validator("texto")
    @classmethod
    def _marcadores_conhecidos(cls, texto: str) -> str:
        desconhecidos = marcadores_desconhecidos(texto)
        if desconhecidos:
            aceitos = ", ".join(f"{{{m}}}" for m in MARCADORES)
            raise ValueError(f"marcador desconhecido {{{desconhecidos[0]}}}; use {aceitos}")
        return texto


class FasePadrao(_Modelo):
    nome: Texto
    objetivo: Texto
    duracao_semanas: int = Field(ge=1)
    escopo: list[Texto] = []
    entregaveis: list[Texto] = []
    escopo_da_revisao: bool = False  # recebe os itens "entra no MVP" da revisão
    investimento_da_sessao: bool = False  # recebe o investimento informado na sessão
    faixas_score_final: list[Id] = []  # vazio: a fase entra sempre


class Padrao(_Modelo):
    """O que a app preenche ao criar uma proposta; o consultor edita depois."""

    validade_dias: int = Field(ge=1)
    condicoes_pagamento: Texto
    impostos: Texto
    reajuste: Texto
    fases: list[FasePadrao] = Field(min_length=1)
    premissas: list[Texto] = []
    responsabilidades: list[Texto] = []

    @model_validator(mode="after")
    def _uma_fase_para_cada_dado_da_sessao(self):
        for campo in ("escopo_da_revisao", "investimento_da_sessao"):
            if sum(getattr(fase, campo) for fase in self.fases) > 1:
                raise ValueError(f"só uma fase pode ter {campo}: true")
        return self


class CriterioDeAceite(_Modelo):
    """Tabela de referência do questionário que entra no critério de aceite."""

    bloco: int = Field(ge=1)
    tabela: Texto


class ModeloProposta(_Modelo):
    versao: int = Field(ge=1)
    titulo: Texto
    aviso: Texto  # o modelo é ponto de partida e deve ser revisado por advogado
    alerta_score_final: list[Id] = []
    criterio_de_aceite: CriterioDeAceite | None = None
    padrao: Padrao
    clausulas: list[Clausula] = Field(min_length=1)

    @model_validator(mode="after")
    def _ids_de_clausula_unicos(self):
        repetidos = [id_ for id_, n in Counter(c.id for c in self.clausulas).items() if n > 1]
        if repetidos:
            raise ValueError(f"id de cláusula repetido: '{repetidos[0]}'")
        return self

    def clausula(self, clausula_id: str) -> Clausula:
        for clausula in self.clausulas:
            if clausula.id == clausula_id:
                return clausula
        raise KeyError(f"o modelo da proposta não tem a cláusula '{clausula_id}'")


def problemas_com_o_questionario(modelo: ModeloProposta, questionario: Questionario) -> list[str]:
    """Referências do modelo que o questionário não tem (lista vazia: tudo certo)."""
    faixas = {f.id for f in questionario.scores.viabilidade_final.faixas}
    problemas = [
        f"alerta_score_final: o score final não tem a faixa '{id_}'"
        for id_ in modelo.alerta_score_final
        if id_ not in faixas
    ]
    for fase in modelo.padrao.fases:
        problemas += [
            f"fase '{fase.nome}': o score final não tem a faixa '{id_}'"
            for id_ in fase.faixas_score_final
            if id_ not in faixas
        ]
    criterio = modelo.criterio_de_aceite
    if criterio is not None:
        try:
            titulos = [r.titulo for r in questionario.bloco(criterio.bloco).referencias]
        except KeyError:
            titulos = []
        if criterio.tabela not in titulos:
            problemas.append(
                f"criterio_de_aceite: o bloco {criterio.bloco} não tem a tabela '{criterio.tabela}'"
            )
    return problemas

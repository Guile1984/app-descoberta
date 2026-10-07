"""Modelos Pydantic do questionário (catálogo YAML).

Os modelos descrevem a forma do arquivo e checam regras que envolvem mais de um campo
(ids únicos, condicionais válidas, faixas dos scores). São imutáveis: o questionário
é carregado uma vez e só lido depois.
"""

from collections import Counter
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NOTA_MAXIMA_POR_CRITERIO = 3
BLOCO_TIPO_SOLUCAO = 3  # o bloco 3 define o tipo de solução, que abre as condicionais

Id = Annotated[str, StringConstraints(pattern=r"^[a-z0-9_.]+$")]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
TipoPergunta = Literal["obrigatoria", "aprofundamento"]


class _Modelo(BaseModel):
    # extra="forbid": um campo com erro de digitação ("texo") vira erro, em vez de ser ignorado.
    model_config = ConfigDict(extra="forbid", frozen=True)


class Condicao(_Modelo):
    """A pergunta só aparece se o tipo de solução da sessão estiver nesta lista."""

    tipos_solucao: list[Id] = Field(min_length=1)


class Pergunta(_Modelo):
    id: Id
    tipo: TipoPergunta
    texto: Texto
    condicao: Condicao | None = None


class Sinal(_Modelo):
    id: Id
    texto: Texto


class Referencia(_Modelo):
    """Tabela de consulta exibida ao consultor (ex.: níveis de integração)."""

    titulo: Texto
    colunas: list[Texto] = Field(min_length=1)
    linhas: list[list[Texto]] = Field(min_length=1)

    @model_validator(mode="after")
    def _linhas_com_todas_as_colunas(self):
        esperado = len(self.colunas)
        for numero, linha in enumerate(self.linhas, start=1):
            if len(linha) != esperado:
                raise ValueError(
                    f"tabela '{self.titulo}': a linha {numero} tem {len(linha)} célula(s), "
                    f"mas a tabela tem {esperado} colunas"
                )
        return self


class Bloco(_Modelo):
    numero: int = Field(ge=1)
    id: Id
    titulo: Texto
    objetivo: Texto
    saida_esperada: Texto
    perguntas: list[Pergunta] = []
    sinais: list[Sinal] = []
    notas: list[Texto] = []
    referencias: list[Referencia] = []
    secoes_relatorio: list[Texto] = []


class TipoSolucao(_Modelo):
    id: Id
    rotulo: Texto
    situacao: Texto


class ItemEncerramento(_Modelo):
    id: Id
    titulo: Texto
    descricao: Texto


class Encerramento(_Modelo):
    objetivo: Texto
    itens: list[ItemEncerramento] = Field(min_length=1)


class _Intervalo(_Modelo):
    """Intervalo fechado [min, max] de pontuação."""

    min: int = Field(ge=0)
    max: int = Field(ge=0)

    @property
    def nome(self) -> str:
        return f"{self.min}–{self.max}"

    @model_validator(mode="after")
    def _min_ate_max(self):
        if self.min > self.max:
            raise ValueError(f"faixa '{self.nome}': min ({self.min}) maior que max ({self.max})")
        return self


class Faixa(_Intervalo):
    """Faixa de um score, com o resultado correspondente (ex.: "MVP com ressalvas")."""

    id: Id
    rotulo: Texto
    descricao: Texto | None = None

    @property
    def nome(self) -> str:
        return self.id


class FaixaNota(_Intervalo):
    """Faixa do score de dados (0–15) que vira uma nota (0–3) do score final."""

    nota: int = Field(ge=0, le=NOTA_MAXIMA_POR_CRITERIO)


class CriterioProntidao(_Modelo):
    id: Id
    rotulo: Texto
    ancora_0: Texto
    ancora_3: Texto


class CriterioViabilidade(_Modelo):
    id: Id
    rotulo: Texto
    blocos_origem: list[int] = Field(min_length=1)


def _problemas_das_faixas(faixas: list[_Intervalo], maximo: int) -> list[str]:
    """Confere se as faixas cobrem 0..maximo sem lacunas nem sobreposições."""
    problemas = [
        f"id de faixa duplicado '{i}'"
        for i, n in Counter(f.id for f in faixas if isinstance(f, Faixa)).items()
        if n > 1
    ]
    ordenadas = sorted(faixas, key=lambda faixa: faixa.min)
    if ordenadas[0].min != 0:
        problemas.append(f"a primeira faixa deve começar em 0 (começa em {ordenadas[0].min})")
    for anterior, atual in zip(ordenadas, ordenadas[1:], strict=False):
        if atual.min <= anterior.max:
            problemas.append(f"as faixas '{anterior.nome}' e '{atual.nome}' se sobrepõem")
        elif atual.min > anterior.max + 1:
            problemas.append(
                f"lacuna entre as faixas '{anterior.nome}' e '{atual.nome}' "
                f"({anterior.max + 1} a {atual.min - 1} não tem faixa)"
            )
    ultima = max(faixa.max for faixa in faixas)
    if ultima != maximo:
        problemas.append(f"as faixas devem terminar no máximo {maximo} (terminam em {ultima})")
    return problemas


class _Score(_Modelo):
    faixas: list[Faixa] = Field(min_length=1)

    @property
    def pontuacao_maxima(self) -> int:
        return NOTA_MAXIMA_POR_CRITERIO * len(self.criterios)

    @model_validator(mode="after")
    def _faixas_cobrem_a_escala(self):
        problemas = _problemas_das_faixas(self.faixas, self.pontuacao_maxima)
        if problemas:
            raise ValueError("; ".join(problemas))
        return self


class ScoreProntidao(_Score):
    criterios: list[CriterioProntidao] = Field(min_length=1)
    # Como o score de dados vira a nota do critério "prontidao_dados" do score final.
    conversao_para_nota: list[FaixaNota] = Field(min_length=1)

    @model_validator(mode="after")
    def _conversao_cobre_a_escala(self):
        problemas = _problemas_das_faixas(self.conversao_para_nota, self.pontuacao_maxima)
        ordenadas = sorted(self.conversao_para_nota, key=lambda faixa: faixa.min)
        for anterior, atual in zip(ordenadas, ordenadas[1:], strict=False):
            if atual.nota < anterior.nota:
                problemas.append(
                    f"a nota não pode diminuir quando o score sobe "
                    f"('{anterior.nome}' vale {anterior.nota}, '{atual.nome}' vale {atual.nota})"
                )
        if problemas:
            raise ValueError("conversao_para_nota: " + "; ".join(problemas))
        return self


class ScoreViabilidade(_Score):
    criterios: list[CriterioViabilidade] = Field(min_length=1)


class Scores(_Modelo):
    prontidao_dados: ScoreProntidao
    viabilidade_final: ScoreViabilidade


class Questionario(_Modelo):
    versao: int = Field(ge=1)
    titulo: Texto
    orientacoes: list[Texto] = []
    tipos_solucao: list[TipoSolucao] = Field(min_length=1)
    blocos: list[Bloco] = Field(min_length=1)
    encerramento: Encerramento
    scores: Scores

    def bloco(self, numero: int) -> Bloco:
        for bloco in self.blocos:
            if bloco.numero == numero:
                return bloco
        raise KeyError(f"o questionário não tem bloco {numero}")

    @model_validator(mode="after")
    def _validar_consistencia(self):
        problemas = [
            *self._problemas_de_numeracao(),
            *self._problemas_de_ids(),
            *self._problemas_de_condicoes(),
            *self._problemas_de_blocos_origem(),
        ]
        if problemas:
            raise ValueError("; ".join(problemas))
        return self

    def _problemas_de_numeracao(self) -> list[str]:
        numeros = [bloco.numero for bloco in self.blocos]
        if numeros != list(range(1, len(numeros) + 1)):
            return [f"os blocos devem ser numerados em sequência a partir de 1 (estão {numeros})"]
        return []

    def _problemas_de_ids(self) -> list[str]:
        ids = [tipo.id for tipo in self.tipos_solucao]
        for bloco in self.blocos:
            ids.append(bloco.id)
            ids.extend(pergunta.id for pergunta in bloco.perguntas)
            ids.extend(sinal.id for sinal in bloco.sinais)
        ids.extend(item.id for item in self.encerramento.itens)
        ids.extend(criterio.id for criterio in self.scores.prontidao_dados.criterios)
        ids.extend(criterio.id for criterio in self.scores.viabilidade_final.criterios)
        return [
            f"id duplicado '{id_}' (aparece {vezes} vezes)"
            for id_, vezes in Counter(ids).items()
            if vezes > 1
        ]

    def _problemas_de_condicoes(self) -> list[str]:
        tipos_existentes = {tipo.id for tipo in self.tipos_solucao}
        problemas = []
        for bloco in self.blocos:
            for pergunta in bloco.perguntas:
                if pergunta.condicao is None:
                    continue
                local = f"pergunta '{pergunta.id}' (bloco {bloco.numero})"
                if bloco.numero <= BLOCO_TIPO_SOLUCAO:
                    problemas.append(
                        f"{local}: perguntas condicionais só podem aparecer depois do bloco "
                        f"{BLOCO_TIPO_SOLUCAO}, que define o tipo de solução"
                    )
                for tipo in pergunta.condicao.tipos_solucao:
                    if tipo not in tipos_existentes:
                        problemas.append(
                            f"{local}: condição cita tipo de solução inexistente '{tipo}'"
                        )
        return problemas

    def _problemas_de_blocos_origem(self) -> list[str]:
        numeros = {bloco.numero for bloco in self.blocos}
        problemas = []
        for criterio in self.scores.viabilidade_final.criterios:
            inexistentes = [n for n in criterio.blocos_origem if n not in numeros]
            if inexistentes:
                problemas.append(
                    f"critério '{criterio.id}': blocos de origem inexistentes {inexistentes}"
                )
        return problemas

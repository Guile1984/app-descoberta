"""Modelos Pydantic do questionário (catálogo YAML).

Os modelos descrevem a forma do arquivo e checam regras que envolvem mais de um campo
(ids únicos, condicionais válidas, faixas dos scores). São imutáveis: o questionário
é carregado uma vez e só lido depois.
"""

import re
from collections import Counter
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NOTA_MAXIMA_POR_CRITERIO = 3
BLOCO_TIPO_SOLUCAO = 3  # o bloco 3 define o tipo de solução, que abre as condicionais

PADRAO_ID = r"^[a-z0-9_.]+$"  # letras minúsculas sem acento, números, "_" e "."

Id = Annotated[str, StringConstraints(pattern=PADRAO_ID)]
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


class SecaoRelatorio(_Modelo):
    """Seção do Relatório de Descoberta; o id liga a seção à sua montagem (relatorio)."""

    id: Id
    titulo: Texto
    blocos: list[int] = []  # blocos cujas respostas obrigatórias entram na seção
    respostas: list[Id] = []  # outras perguntas ou itens do encerramento
    tabelas: list[Texto] = []  # tabelas de referência (títulos) dos blocos acima

    @property
    def titulo_para_cliente(self) -> str:
        """O título sem o parêntese final, que é nota para o consultor: "(bloco 4)" ou
        "(meia página, lido em 2 minutos)"."""
        return re.sub(r"\s*\([^)]*\)$", "", self.titulo)


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
    secoes_relatorio: list[SecaoRelatorio] = []


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


class CategoriaRisco(_Modelo):
    id: Id
    rotulo: Texto


class TextoRevisao(_Modelo):
    """Parte narrativa do relatório, escrita pelo consultor na revisão pós-sessão."""

    id: Id
    titulo: Texto
    orientacao: Texto
    # Perguntas ou itens do encerramento cujas respostas aparecem ao lado, para consulta.
    apoio: list[Id] = []


class Revisao(_Modelo):
    """O que a revisão pós-sessão pede, além das respostas: as saídas para o relatório."""

    categorias_risco: list[CategoriaRisco] = Field(min_length=1)
    textos: list[TextoRevisao] = Field(min_length=1)


class Duracao(_Modelo):
    """Duração-alvo da sessão: o cronômetro muda de cor no aviso e de novo no limite."""

    aviso_minutos: int = Field(ge=1)
    limite_minutos: int = Field(ge=1)

    @model_validator(mode="after")
    def _aviso_antes_do_limite(self):
        if self.aviso_minutos >= self.limite_minutos:
            raise ValueError(
                f"o aviso ({self.aviso_minutos} min) precisa vir antes do limite "
                f"({self.limite_minutos} min)"
            )
        return self


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
    bloco: int = Field(ge=1)  # bloco onde as notas do score são dadas durante a sessão
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
    # Critério do score final cuja nota não é dada à mão: sai deste score pela conversão.
    criterio_final: Id
    # Como o score de dados vira a nota desse critério do score final.
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
    duracao: Duracao
    tipos_solucao: list[TipoSolucao] = Field(min_length=1)
    blocos: list[Bloco] = Field(min_length=1)
    encerramento: Encerramento
    revisao: Revisao
    scores: Scores

    def bloco(self, numero: int) -> Bloco:
        for bloco in self.blocos:
            if bloco.numero == numero:
                return bloco
        raise KeyError(f"o questionário não tem bloco {numero}")

    def pergunta(self, pergunta_id: str) -> tuple[Bloco, Pergunta]:
        """A pergunta com esse id e o bloco onde ela está."""
        for bloco in self.blocos:
            for pergunta in bloco.perguntas:
                if pergunta.id == pergunta_id:
                    return bloco, pergunta
        raise KeyError(f"o questionário não tem a pergunta '{pergunta_id}'")

    def item_encerramento(self, item_id: str) -> ItemEncerramento:
        for item in self.encerramento.itens:
            if item.id == item_id:
                return item
        raise KeyError(f"o encerramento não tem o item '{item_id}'")

    def categoria_risco(self, categoria_id: str) -> CategoriaRisco:
        for categoria in self.revisao.categorias_risco:
            if categoria.id == categoria_id:
                return categoria
        raise KeyError(f"o questionário não tem a categoria de risco '{categoria_id}'")

    def texto_revisao(self, texto_id: str) -> TextoRevisao:
        for texto in self.revisao.textos:
            if texto.id == texto_id:
                return texto
        raise KeyError(f"o questionário não tem o texto de revisão '{texto_id}'")

    @model_validator(mode="after")
    def _validar_consistencia(self):
        problemas = [
            *self._problemas_de_numeracao(),
            *self._problemas_de_ids(),
            *self._problemas_de_condicoes(),
            *self._problemas_de_blocos_origem(),
            *self._problemas_dos_scores(),
            *self._problemas_do_apoio(),
            *self._problemas_das_secoes(),
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
            ids.extend(secao.id for secao in bloco.secoes_relatorio)
        ids.extend(item.id for item in self.encerramento.itens)
        ids.extend(criterio.id for criterio in self.scores.prontidao_dados.criterios)
        ids.extend(criterio.id for criterio in self.scores.viabilidade_final.criterios)
        ids.extend(categoria.id for categoria in self.revisao.categorias_risco)
        ids.extend(texto.id for texto in self.revisao.textos)
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

    def _problemas_dos_scores(self) -> list[str]:
        numeros = {bloco.numero for bloco in self.blocos}
        problemas = [
            f"score '{nome}': bloco {score.bloco} inexistente"
            for nome, score in (
                ("prontidao_dados", self.scores.prontidao_dados),
                ("viabilidade_final", self.scores.viabilidade_final),
            )
            if score.bloco not in numeros
        ]
        criterio_final = self.scores.prontidao_dados.criterio_final
        if criterio_final not in {c.id for c in self.scores.viabilidade_final.criterios}:
            problemas.append(
                f"prontidao_dados.criterio_final: '{criterio_final}' não é critério "
                "do score viabilidade_final"
            )
        return problemas

    def _problemas_do_apoio(self) -> list[str]:
        existentes = {p.id for bloco in self.blocos for p in bloco.perguntas}
        existentes |= {item.id for item in self.encerramento.itens}
        return [
            f"revisao: texto '{texto.id}' cita no apoio '{id_}', que não é pergunta nem "
            "item do encerramento"
            for texto in self.revisao.textos
            for id_ in texto.apoio
            if id_ not in existentes
        ]

    def _problemas_das_secoes(self) -> list[str]:
        numeros = {bloco.numero: bloco for bloco in self.blocos}
        existentes = {p.id for bloco in self.blocos for p in bloco.perguntas}
        existentes |= {item.id for item in self.encerramento.itens}
        problemas = []
        for bloco in self.blocos:
            for secao in bloco.secoes_relatorio:
                local = f"seção '{secao.id}'"
                problemas += [
                    f"{local}: bloco {n} inexistente" for n in secao.blocos if n not in numeros
                ]
                problemas += [
                    f"{local}: resposta '{id_}' não é pergunta nem item do encerramento"
                    for id_ in secao.respostas
                    if id_ not in existentes
                ]
                titulos = {
                    r.titulo for n in secao.blocos if n in numeros for r in numeros[n].referencias
                }
                problemas += [
                    f"{local}: tabela '{t}' não está nos blocos {secao.blocos}"
                    for t in secao.tabelas
                    if t not in titulos
                ]
        return problemas

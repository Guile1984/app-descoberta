"""Revisão pós-sessão: matriz de riscos 3×3 e o que ainda falta para o relatório.

As funções recebem qualquer objeto com os atributos certos (as tabelas do repositório ou,
nos testes, dataclasses simples); o domínio não conhece o banco.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum, auto
from typing import Protocol


class Nivel(StrEnum):
    """Probabilidade e impacto de um risco (bloco 7: baixo/médio/alto)."""

    baixo = auto()
    medio = auto()
    alto = auto()


class Camada(StrEnum):
    """Camada do indicador (bloco 5, "Duas camadas de métricas")."""

    negocio = auto()
    tecnica = auto()


class Responsavel(StrEnum):
    cliente = auto()
    consultor = auto()


NIVEIS = list(Nivel)  # do mais baixo para o mais alto


class RiscoLike(Protocol):
    descricao: str
    probabilidade: str
    impacto: str
    mitigacao: str | None


class IndicadorLike(Protocol):
    nome: str
    camada: str
    valor_atual: str | None
    meta: str | None
    prazo: str | None
    como_medir: str | None


class ItemEscopoLike(Protocol):
    texto: str
    entra: bool


class ProximoPassoLike(Protocol):
    acao: str
    prazo: date | None


# --- Matriz de riscos ---


def severidade(probabilidade: str, impacto: str) -> Nivel:
    """Nível da célula: somando as posições (0 a 2) dos dois eixos, 0–1 é baixo, 2 é médio
    e 3–4 é alto. Assim alto × alto, alto × médio e médio × alto são células altas."""
    soma = NIVEIS.index(Nivel(probabilidade)) + NIVEIS.index(Nivel(impacto))
    if soma <= 1:
        return Nivel.baixo
    return Nivel.medio if soma == 2 else Nivel.alto


@dataclass(frozen=True)
class Celula:
    probabilidade: Nivel
    impacto: Nivel
    severidade: Nivel
    # (número do risco, risco): o número é a posição na lista, começando em 1 (R1, R2…).
    riscos: list[tuple[int, RiscoLike]] = field(default_factory=list)


def matriz_de_riscos(riscos: Sequence[RiscoLike]) -> list[list[Celula]]:
    """Grade 3×3 como se desenha no papel: linhas do impacto alto para o baixo, colunas da
    probabilidade baixa para a alta (o canto de cima à direita é o mais grave)."""
    matriz = [[Celula(p, i, severidade(p, i)) for p in NIVEIS] for i in reversed(NIVEIS)]
    for numero, risco in enumerate(riscos, start=1):
        linha = len(NIVEIS) - 1 - NIVEIS.index(Nivel(risco.impacto))
        coluna = NIVEIS.index(Nivel(risco.probabilidade))
        matriz[linha][coluna].riscos.append((numero, risco))
    return matriz


# --- O que falta preencher ---


def _vazio(texto: str | None) -> bool:
    return texto is None or not texto.strip()


def _juntar(itens: list[str]) -> str:
    """["a", "b", "c"] → "a, b e c"."""
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


@dataclass(frozen=True)
class PendenciasRevisao:
    textos: list[str]  # ids dos textos em branco
    riscos: list[str]
    indicadores: list[str]
    escopo: list[str]
    proximos_passos: list[str]

    @property
    def total(self) -> int:
        return sum(
            len(lista)
            for lista in (
                self.textos,
                self.riscos,
                self.indicadores,
                self.escopo,
                self.proximos_passos,
            )
        )


def _pendencias_dos_riscos(riscos: Sequence[RiscoLike]) -> list[str]:
    if not riscos:
        return ["nenhum risco cadastrado"]
    # Bloco 7: riscos altos nos dois eixos exigem mitigação definida antes do início.
    return [
        f"“{r.descricao}”: probabilidade e impacto altos exigem mitigação antes do início"
        for r in riscos
        if Nivel(r.probabilidade) == Nivel(r.impacto) == Nivel.alto and _vazio(r.mitigacao)
    ]


# Colunas da tabela do bloco 5: "indicador atual → meta → prazo → como medir".
_COLUNAS_INDICADOR = {
    "valor_atual": "valor atual",
    "meta": "meta",
    "prazo": "prazo",
    "como_medir": "como medir",
}


def _pendencias_dos_indicadores(indicadores: Sequence[IndicadorLike]) -> list[str]:
    pendencias = []
    if not any(Camada(i.camada) == Camada.negocio for i in indicadores):
        pendencias.append("nenhum indicador de negócio")
    for indicador in indicadores:
        faltam = [
            rotulo
            for campo, rotulo in _COLUNAS_INDICADOR.items()
            if _vazio(getattr(indicador, campo))
        ]
        if faltam:
            pendencias.append(f"“{indicador.nome}”: falta {_juntar(faltam)}")
    return pendencias


def _pendencias_do_escopo(itens: Sequence[ItemEscopoLike]) -> list[str]:
    pendencias = []
    if not any(item.entra for item in itens):
        pendencias.append("nenhum item que entra no MVP")
    if all(item.entra for item in itens):
        pendencias.append("nenhum item que fica fora do MVP")
    return pendencias


def _pendencias_dos_passos(passos: Sequence[ProximoPassoLike]) -> list[str]:
    if not passos:
        return ["nenhum próximo passo"]
    return [f"“{passo.acao}”: sem prazo" for passo in passos if passo.prazo is None]


def pendencias_da_revisao(
    ids_textos: Sequence[str],
    textos: Mapping[str, str],
    riscos: Sequence[RiscoLike],
    indicadores: Sequence[IndicadorLike],
    itens_escopo: Sequence[ItemEscopoLike],
    proximos_passos: Sequence[ProximoPassoLike],
) -> PendenciasRevisao:
    """O que ainda falta para o relatório, seção por seção (listas vazias: nada falta).

    `ids_textos` são os textos que o questionário pede, na ordem; `textos`, os escritos.
    """
    return PendenciasRevisao(
        textos=[id_ for id_ in ids_textos if _vazio(textos.get(id_))],
        riscos=_pendencias_dos_riscos(riscos),
        indicadores=_pendencias_dos_indicadores(indicadores),
        escopo=_pendencias_do_escopo(itens_escopo),
        proximos_passos=_pendencias_dos_passos(proximos_passos),
    )

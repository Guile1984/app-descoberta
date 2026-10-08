"""Score de prontidão de dados (bloco 4) e score final de viabilidade (bloco 10).

Critérios, faixas e a conversão entre os dois scores vêm do questionário (YAML).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from descoberta.questionario import Faixa, Questionario
from descoberta.questionario.modelos import NOTA_MAXIMA_POR_CRITERIO

from .faixas import classificar


@dataclass(frozen=True)
class ResultadoScore:
    pontuacao: int
    maximo: int
    faixa: Faixa


@dataclass(frozen=True)
class ScoreParcial:
    """Score durante a sessão, quando parte das notas ainda não foi dada.

    `pontuacao` soma só as notas já dadas; `resultado` (com a faixa) só existe quando
    não falta nenhuma.
    """

    pontuacao: int
    maximo: int
    faltando: tuple[str, ...]
    resultado: ResultadoScore | None


def _conferir_notas(notas: Mapping[str, int], criterios: Iterable[str]) -> tuple[str, ...]:
    """Recusa critério desconhecido e nota fora de 0 a 3; devolve os critérios sem nota."""
    esperados = list(criterios)
    desconhecidos = [c for c in notas if c not in esperados]
    if desconhecidos:
        raise ValueError(f"critério desconhecido {', '.join(desconhecidos)}")
    for criterio, nota in notas.items():
        if isinstance(nota, bool) or not isinstance(nota, int):
            raise TypeError(f"nota de {criterio} precisa ser inteira (recebido {nota!r})")
        if not 0 <= nota <= NOTA_MAXIMA_POR_CRITERIO:
            raise ValueError(
                f"nota de {criterio} deve ficar entre 0 e {NOTA_MAXIMA_POR_CRITERIO} "
                f"(recebido {nota})"
            )
    return tuple(c for c in esperados if c not in notas)


def _somar_notas(notas: Mapping[str, int], criterios: Iterable[str]) -> int:
    """Confere que há uma nota de 0 a 3 para cada critério, e só para eles; devolve a soma."""
    faltando = _conferir_notas(notas, criterios)
    if faltando:
        raise ValueError(f"faltando nota para {', '.join(faltando)}")
    return sum(notas.values())


def _parcial(notas: Mapping[str, int], score, calcular) -> ScoreParcial:
    faltando = _conferir_notas(notas, (c.id for c in score.criterios))
    resultado = None if faltando else calcular()
    return ScoreParcial(sum(notas.values()), score.pontuacao_maxima, faltando, resultado)


def score_prontidao(notas: Mapping[str, int], questionario: Questionario) -> ResultadoScore:
    score = questionario.scores.prontidao_dados
    pontuacao = _somar_notas(notas, (c.id for c in score.criterios))
    return ResultadoScore(pontuacao, score.pontuacao_maxima, classificar(pontuacao, score.faixas))


def score_prontidao_parcial(notas: Mapping[str, int], questionario: Questionario) -> ScoreParcial:
    return _parcial(
        notas,
        questionario.scores.prontidao_dados,
        lambda: score_prontidao(notas, questionario),
    )


def score_viabilidade_parcial(notas: Mapping[str, int], questionario: Questionario) -> ScoreParcial:
    return _parcial(
        notas,
        questionario.scores.viabilidade_final,
        lambda: score_viabilidade(notas, questionario),
    )


def nota_prontidao_para_viabilidade(score: int, questionario: Questionario) -> int:
    """Converte o score de dados (0–15) na nota do critério prontidao_dados (0–3)."""
    conversao = questionario.scores.prontidao_dados.conversao_para_nota
    return classificar(score, conversao).nota


def score_viabilidade(notas: Mapping[str, int], questionario: Questionario) -> ResultadoScore:
    score = questionario.scores.viabilidade_final
    pontuacao = _somar_notas(notas, (c.id for c in score.criterios))
    return ResultadoScore(pontuacao, score.pontuacao_maxima, classificar(pontuacao, score.faixas))

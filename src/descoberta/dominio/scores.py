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


def _somar_notas(notas: Mapping[str, int], criterios: Iterable[str]) -> int:
    """Confere que há uma nota de 0 a 3 para cada critério, e só para eles; devolve a soma."""
    esperados = list(criterios)
    faltando = [c for c in esperados if c not in notas]
    desconhecidos = [c for c in notas if c not in esperados]
    if faltando or desconhecidos:
        partes = []
        if faltando:
            partes.append(f"faltando nota para {', '.join(faltando)}")
        if desconhecidos:
            partes.append(f"critério desconhecido {', '.join(desconhecidos)}")
        raise ValueError("; ".join(partes))
    for criterio, nota in notas.items():
        if isinstance(nota, bool) or not isinstance(nota, int):
            raise TypeError(f"nota de {criterio} precisa ser inteira (recebido {nota!r})")
        if not 0 <= nota <= NOTA_MAXIMA_POR_CRITERIO:
            raise ValueError(
                f"nota de {criterio} deve ficar entre 0 e {NOTA_MAXIMA_POR_CRITERIO} "
                f"(recebido {nota})"
            )
    return sum(notas.values())


def score_prontidao(notas: Mapping[str, int], questionario: Questionario) -> ResultadoScore:
    score = questionario.scores.prontidao_dados
    pontuacao = _somar_notas(notas, (c.id for c in score.criterios))
    return ResultadoScore(pontuacao, score.pontuacao_maxima, classificar(pontuacao, score.faixas))


def nota_prontidao_para_viabilidade(score: int, questionario: Questionario) -> int:
    """Converte o score de dados (0–15) na nota do critério prontidao_dados (0–3)."""
    conversao = questionario.scores.prontidao_dados.conversao_para_nota
    return classificar(score, conversao).nota


def score_viabilidade(notas: Mapping[str, int], questionario: Questionario) -> ResultadoScore:
    score = questionario.scores.viabilidade_final
    pontuacao = _somar_notas(notas, (c.id for c in score.criterios))
    return ResultadoScore(pontuacao, score.pontuacao_maxima, classificar(pontuacao, score.faixas))

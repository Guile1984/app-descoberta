"""Cronômetro da sessão: tempo decorrido (com pausas) e cor conforme a duração-alvo."""

from datetime import datetime, timedelta
from typing import Literal

from descoberta.questionario import Duracao

SituacaoTempo = Literal["normal", "atencao", "limite"]


def tempo_decorrido(
    acumulado_segundos: int, rodando_desde: datetime | None, agora: datetime
) -> timedelta:
    """Tempo das partes já encerradas (acumulado) mais o trecho atual, se estiver rodando."""
    if acumulado_segundos < 0:
        raise ValueError(f"tempo acumulado não pode ser negativo (recebido {acumulado_segundos})")
    decorrido = timedelta(seconds=acumulado_segundos)
    if rodando_desde is not None:
        # Se o relógio do notebook voltar no tempo, o trecho atual conta zero.
        decorrido += max(agora - rodando_desde, timedelta(0))
    return decorrido


def situacao_do_tempo(decorrido: timedelta, duracao: Duracao) -> SituacaoTempo:
    """Normal até o aviso; atenção do aviso até o limite; limite dali em diante."""
    minutos = decorrido / timedelta(minutes=1)
    if minutos >= duracao.limite_minutos:
        return "limite"
    if minutos >= duracao.aviso_minutos:
        return "atencao"
    return "normal"

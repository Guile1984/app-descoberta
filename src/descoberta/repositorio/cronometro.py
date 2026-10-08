"""Cronômetro da sessão: um único botão (ou atalho) que inicia, pausa e retoma."""

from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from descoberta.dominio.cronometro import tempo_decorrido

from ._comum import exigir_sessao, gravar
from .modelos import Cronometro, agora


def _em_utc(horario: datetime | None) -> datetime | None:
    # O SQLite guarda o horário sem fuso; tudo o que gravamos está em UTC.
    if horario is None or horario.tzinfo is not None:
        return horario
    return horario.replace(tzinfo=UTC)


def obter_cronometro(session: Session, sessao_id: int) -> Cronometro | None:
    cronometro = session.get(Cronometro, sessao_id)
    if cronometro is not None:
        cronometro.rodando_desde = _em_utc(cronometro.rodando_desde)
    return cronometro


def alternar_cronometro(
    session: Session, sessao_id: int, momento: datetime | None = None
) -> Cronometro:
    """Inicia (ou retoma) se estiver parado; pausa se estiver rodando."""
    momento = momento or agora()
    exigir_sessao(session, sessao_id)
    cronometro = obter_cronometro(session, sessao_id) or Cronometro(sessao_id=sessao_id)
    if cronometro.rodando_desde is None:
        cronometro.rodando_desde = momento
    else:
        decorrido = tempo_decorrido(
            cronometro.acumulado_segundos, cronometro.rodando_desde, momento
        )
        cronometro.acumulado_segundos = int(decorrido.total_seconds())
        cronometro.rodando_desde = None
    gravar(session, cronometro)
    cronometro.rodando_desde = _em_utc(cronometro.rodando_desde)
    return cronometro


def tempo_do_cronometro(
    session: Session, sessao_id: int, momento: datetime | None = None
) -> tuple[timedelta, bool]:
    """Tempo decorrido até `momento` e se o cronômetro está rodando."""
    cronometro = obter_cronometro(session, sessao_id)
    if cronometro is None:
        return timedelta(0), False
    decorrido = tempo_decorrido(
        cronometro.acumulado_segundos, cronometro.rodando_desde, momento or agora()
    )
    return decorrido, cronometro.rodando_desde is not None

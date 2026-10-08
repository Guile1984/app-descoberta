"""Cronômetro da sessão: iniciar, pausar e retomar, com o tempo guardado no banco."""

from datetime import UTC, datetime, timedelta

import pytest

from descoberta.repositorio import (
    RegistroNaoEncontrado,
    alternar_cronometro,
    excluir_sessao,
    obter_cronometro,
    tempo_do_cronometro,
)

INICIO = datetime(2026, 10, 8, 14, 0, tzinfo=UTC)


def test_sessao_sem_cronometro(session, sessao):
    assert obter_cronometro(session, sessao.id) is None
    assert tempo_do_cronometro(session, sessao.id, INICIO) == (timedelta(0), False)


def test_iniciar(session, sessao):
    cronometro = alternar_cronometro(session, sessao.id, INICIO)
    assert cronometro.acumulado_segundos == 0
    agora = INICIO + timedelta(minutes=3)
    assert tempo_do_cronometro(session, sessao.id, agora) == (timedelta(minutes=3), True)


def test_pausar_guarda_o_tempo_e_retomar_continua_dele(session, sessao):
    alternar_cronometro(session, sessao.id, INICIO)
    alternar_cronometro(session, sessao.id, INICIO + timedelta(minutes=10))  # pausa
    session.expire_all()
    parado = INICIO + timedelta(hours=1)
    assert tempo_do_cronometro(session, sessao.id, parado) == (timedelta(minutes=10), False)

    alternar_cronometro(session, sessao.id, parado)  # retoma
    assert tempo_do_cronometro(session, sessao.id, parado + timedelta(minutes=5)) == (
        timedelta(minutes=15),
        True,
    )


def test_horario_volta_do_banco_com_fuso(session, sessao):
    # O SQLite não guarda o fuso; o repositório devolve sempre em UTC.
    alternar_cronometro(session, sessao.id, INICIO)
    session.expire_all()
    assert obter_cronometro(session, sessao.id).rodando_desde == INICIO


def test_sem_horario_usa_o_relogio(session, sessao):
    antes = datetime.now(UTC)
    cronometro = alternar_cronometro(session, sessao.id)
    assert antes <= cronometro.rodando_desde <= datetime.now(UTC)


def test_sessao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        alternar_cronometro(session, 999, INICIO)


def test_excluir_a_sessao_apaga_o_cronometro(session, sessao):
    sessao_id = sessao.id
    alternar_cronometro(session, sessao_id, INICIO)
    excluir_sessao(session, sessao_id)
    session.expire_all()
    assert obter_cronometro(session, sessao_id) is None

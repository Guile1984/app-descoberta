"""Cronômetro da sessão: tempo decorrido com pausas e cor conforme a duração-alvo."""

from datetime import UTC, datetime, timedelta

import pytest

from descoberta.dominio.cronometro import situacao_do_tempo, tempo_decorrido

INICIO = datetime(2026, 10, 8, 14, 0, tzinfo=UTC)


def test_parado_mostra_so_o_acumulado():
    assert tempo_decorrido(600, None, INICIO) == timedelta(minutes=10)


def test_rodando_soma_o_trecho_atual():
    agora = INICIO + timedelta(minutes=5)
    assert tempo_decorrido(600, INICIO, agora) == timedelta(minutes=15)


def test_relogio_atrasado_nao_gera_tempo_negativo():
    assert tempo_decorrido(60, INICIO, INICIO - timedelta(minutes=1)) == timedelta(minutes=1)


def test_acumulado_negativo_e_recusado():
    with pytest.raises(ValueError, match="negativo"):
        tempo_decorrido(-1, None, INICIO)


@pytest.mark.parametrize(
    ("minutos", "situacao"),
    [
        (0, "normal"),
        (74, "normal"),
        (75, "atencao"),
        (89, "atencao"),
        (90, "limite"),
        (130, "limite"),
    ],
)
def test_situacao_segue_os_limites_do_questionario(questionario_v1, minutos, situacao):
    assert situacao_do_tempo(timedelta(minutes=minutos), questionario_v1.duracao) == situacao

"""Cronômetro no topo da sessão: inicia, pausa e muda de cor conforme a duração-alvo."""

from datetime import timedelta

import pytest

from descoberta.repositorio import Cronometro, obter_cronometro
from descoberta.repositorio.modelos import agora
from descoberta.web.app import PASTA_STATIC

HX = {"HX-Request": "true"}


def test_pagina_mostra_o_cronometro_parado(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert 'id="cronometro"' in html
    assert "00:00" in html
    assert "Iniciar" in html
    assert "every 30s" not in html  # parado, não precisa se atualizar


def test_iniciar_e_pausar(cliente_http, banco, sessao):
    resposta = cliente_http.post(f"/sessoes/{sessao.id}/cronometro", headers=HX)
    assert resposta.status_code == 200
    assert "Pausar" in resposta.text
    assert 'hx-trigger="every 30s"' in resposta.text  # rodando: atualiza sozinho
    banco.expire_all()
    assert obter_cronometro(banco, sessao.id).rodando_desde is not None

    resposta = cliente_http.post(f"/sessoes/{sessao.id}/cronometro", headers=HX)
    assert "Retomar" in resposta.text
    banco.expire_all()
    assert obter_cronometro(banco, sessao.id).rodando_desde is None


def _rodando_ha(banco, sessao_id, minutos):
    banco.add(Cronometro(sessao_id=sessao_id, rodando_desde=agora() - timedelta(minutes=minutos)))
    banco.commit()


@pytest.mark.parametrize(
    ("minutos", "classe", "texto"),
    [(10, "normal", "00:10"), (80, "atencao", "01:20"), (95, "limite", "01:35")],
)
def test_cor_conforme_a_duracao_alvo(cliente_http, banco, sessao, minutos, classe, texto):
    _rodando_ha(banco, sessao.id, minutos)
    html = cliente_http.get(f"/sessoes/{sessao.id}/cronometro", headers=HX).text
    assert f"cronometro {classe}" in html
    assert texto in html


def test_limites_vem_do_questionario(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}/cronometro", headers=HX).text
    assert "75 min" in html
    assert "90 min" in html


def test_ponto_pulsando_so_enquanto_roda(cliente_http, sessao):
    # Com hh:mm, o primeiro minuto parece parado: o ponto mostra que o tempo está correndo.
    parado = cliente_http.get(f"/sessoes/{sessao.id}/cronometro", headers=HX).text
    assert 'class="pulso"' not in parado
    rodando = cliente_http.post(f"/sessoes/{sessao.id}/cronometro", headers=HX).text
    assert 'class="pulso"' in rodando
    pausado = cliente_http.post(f"/sessoes/{sessao.id}/cronometro", headers=HX).text
    assert 'class="pulso"' not in pausado


def test_pulso_respeita_quem_desativou_animacoes():
    css = (PASTA_STATIC / "estilo.css").read_text(encoding="utf-8")
    assert "@keyframes pulso" in css
    assert "prefers-reduced-motion" in css

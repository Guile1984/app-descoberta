"""Faixa "Banco de demonstração" em todas as telas quando o banco aberto é o data/demo.db."""

from pathlib import Path

from fastapi.testclient import TestClient

from descoberta.web.app import criar_app

RAIZ_PROJETO = Path(__file__).resolve().parents[2]

FAIXA = "Banco de demonstração"


def test_faixa_aparece_com_o_banco_demo(cliente_demo):
    cliente, sessao_id = cliente_demo
    for url in ("/", "/perfil", f"/sessoes/{sessao_id}", "/nao-existe"):
        assert FAIXA in cliente.get(url).text, url


def test_faixa_nao_aparece_com_o_banco_real(cliente_http, perfil):
    for url in ("/", "/perfil", "/nao-existe"):
        assert FAIXA not in cliente_http.get(url).text, url


def test_faixa_vale_para_o_banco_da_variavel_de_ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("DESCOBERTA_BANCO", str(tmp_path / "demo.db"))
    app = criar_app(pasta_config=RAIZ_PROJETO / "config")
    with TestClient(app, base_url="http://127.0.0.1") as cliente:
        assert FAIXA in cliente.get("/perfil").text


def test_rota_de_identidade_para_o_inicializador(cliente_http):
    from descoberta.iniciar import IDENTIDADE

    resposta = cliente_http.get("/_identidade")
    assert resposta.status_code == 200
    assert resposta.text == IDENTIDADE

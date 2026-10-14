"""A configuração do LLM é carregada e conferida quando a app liga."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from descoberta.llm.configuracao import ConfiguracaoLLMInvalida, Provedor
from descoberta.web.app import criar_app

RAIZ_CONFIG = Path(__file__).resolve().parents[2] / "config"


def test_app_liga_com_o_llm_desligado(cliente_http, app):
    assert app.state.config_llm.provedor is Provedor.desligado
    assert app.state.config_llm.claude.modelo == "claude-opus-5-5"


def test_variavel_de_ambiente_liga_o_provedor(monkeypatch, tmp_path):
    monkeypatch.setenv("DESCOBERTA_LLM_PROVEDOR", "ollama")
    app = criar_app(caminho_banco=tmp_path / "t.db", pasta_config=RAIZ_CONFIG)
    with TestClient(app, base_url="http://127.0.0.1"):
        assert app.state.config_llm.provedor is Provedor.ollama


def test_provedor_invalido_impede_a_app_de_ligar(monkeypatch, tmp_path):
    monkeypatch.setenv("DESCOBERTA_LLM_PROVEDOR", "gpt")
    app = criar_app(caminho_banco=tmp_path / "t.db", pasta_config=RAIZ_CONFIG)
    with (
        pytest.raises(ConfiguracaoLLMInvalida, match="DESCOBERTA_LLM_PROVEDOR"),
        TestClient(app, base_url="http://127.0.0.1"),
    ):
        pass

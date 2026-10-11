"""Fixtures dos testes da camada web: a app roda de verdade, com um banco temporário."""

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from descoberta.demo import popular_demo
from descoberta.repositorio import criar_cliente, criar_sessao
from descoberta.web.app import criar_app

RAIZ_PROJETO = Path(__file__).resolve().parents[2]


@pytest.fixture
def app(tmp_path):
    return criar_app(caminho_banco=tmp_path / "teste.db", pasta_config=RAIZ_PROJETO / "config")


@pytest.fixture
def cliente_http(app):
    # O "with" liga a app (abre o banco, carrega o questionário) e a desliga no fim.
    # follow_redirects=False: os testes conferem o redirecionamento em si.
    with TestClient(app, follow_redirects=False) as cliente:
        yield cliente


@pytest.fixture
def banco(app, cliente_http):
    """Sessão do banco para preparar dados e conferir o que a tela gravou."""
    with Session(app.state.engine) as session:
        yield session


@pytest.fixture
def cliente(banco):
    return criar_cliente(banco, nome="Roberto", empresa="Construtora Alvorada")


@pytest.fixture
def sessao(banco, cliente):
    return criar_sessao(banco, cliente_id=cliente.id, data=date(2026, 10, 7), versao_questionario=1)


@pytest.fixture
def app_demo(tmp_path):
    """App com o banco de demonstração (caso Roberto completo) e o id da sessão."""
    caminho = tmp_path / "demo.db"
    sessao_id = popular_demo(caminho)
    return criar_app(caminho_banco=caminho, pasta_config=RAIZ_PROJETO / "config"), sessao_id


@pytest.fixture
def cliente_demo(app_demo):
    app, sessao_id = app_demo
    with TestClient(app, follow_redirects=False) as cliente:
        yield cliente, sessao_id


@pytest.fixture
def app_demo_banco(app_demo, cliente_demo):
    """Abre uma sessão nova do banco de demonstração (vê o que a tela acabou de gravar)."""
    app, _ = app_demo
    abertas = []

    def abrir():
        session = Session(app.state.engine)
        abertas.append(session)
        return session

    yield abrir
    for session in abertas:
        session.close()

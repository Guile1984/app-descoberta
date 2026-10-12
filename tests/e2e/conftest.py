"""Testes no navegador (Playwright): a app roda de verdade, num servidor local temporário.

Todos os testes desta pasta são marcados como e2e. Para rodar só os rápidos:

    uv run pytest -m "not e2e"

Na primeira vez, é preciso baixar o navegador: uv run playwright install chromium
"""

import socket
import threading
import time
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pytest
import uvicorn
from sqlmodel import Session

from descoberta.demo import popular_demo
from descoberta.llm.falso import ProvedorFalso
from descoberta.repositorio import criar_cliente, criar_sessao
from descoberta.web.app import criar_app

RAIZ_PROJETO = Path(__file__).resolve().parents[2]


def pytest_collection_modifyitems(items):
    pasta = Path(__file__).parent
    for item in items:
        if pasta in Path(item.fspath).parents:
            item.add_marker(pytest.mark.e2e)


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def _rodando(app):
    """Liga a app numa porta livre, numa thread, e desliga no fim."""
    porta = _porta_livre()
    servidor = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=porta, log_level="warning")
    )
    thread = threading.Thread(target=servidor.run, daemon=True)
    thread.start()
    limite = time.monotonic() + 10
    while not servidor.started:
        if time.monotonic() > limite:
            raise RuntimeError("o servidor de teste não subiu em 10 s")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{porta}"
    servidor.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
def servidor(tmp_path):
    """A app com um banco temporário vazio."""
    app = criar_app(caminho_banco=tmp_path / "e2e.db", pasta_config=RAIZ_PROJETO / "config")
    with _rodando(app) as base:
        yield app, base


# Resposta do LLM falso, com os marcadores da anonimização (voltam como nomes na tela).
RESPOSTA_DO_LLM_FALSO = (
    "Seguir com fase 0 para a [EMPRESA]: o [PESSOA_1] valida o critério de gravidade."
)


@pytest.fixture
def servidor_demo(tmp_path):
    """A app com o caso Roberto do demo e um LLM falso (nada sai da máquina)."""
    caminho = tmp_path / "demo.db"
    sessao_id = popular_demo(caminho, hoje=date(2026, 10, 11))
    falso = ProvedorFalso(RESPOSTA_DO_LLM_FALSO)
    app = criar_app(caminho_banco=caminho, pasta_config=RAIZ_PROJETO / "config", provedor_llm=falso)
    with _rodando(app) as base:
        yield app, f"{base}/sessoes/{sessao_id}", sessao_id, falso


@pytest.fixture
def banco(servidor):
    app, _ = servidor
    with Session(app.state.engine) as session:
        yield session


@pytest.fixture
def url_sessao(servidor, banco):
    _, base = servidor
    cliente = criar_cliente(banco, nome="Roberto", empresa="Construtora Alvorada")
    sessao = criar_sessao(
        banco, cliente_id=cliente.id, data=date(2026, 10, 8), versao_questionario=1
    )
    return f"{base}/sessoes/{sessao.id}", sessao.id

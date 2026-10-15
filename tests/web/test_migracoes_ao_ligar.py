"""A app aplica as migrações do banco ao ligar, antes do primeiro pedido."""

from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from descoberta.demo import popular_demo
from descoberta.repositorio import criar_engine, revisao_atual, revisao_mais_recente
from descoberta.web.app import criar_app

RAIZ_PROJETO = Path(__file__).resolve().parents[2]


def _ligar(caminho):
    app = criar_app(caminho_banco=caminho, pasta_config=RAIZ_PROJETO / "config")
    with TestClient(app, base_url="http://127.0.0.1") as cliente:
        return cliente.get("/")


def test_banco_novo_e_migrado_ao_ligar(tmp_path):
    caminho = tmp_path / "novo.db"
    assert _ligar(caminho).status_code == 200
    engine = criar_engine(caminho)
    assert revisao_atual(engine) == revisao_mais_recente()
    engine.dispose()


def test_banco_legado_e_reconhecido_ao_ligar(tmp_path):
    caminho = tmp_path / "demo.db"
    popular_demo(caminho, hoje=date(2026, 10, 7))
    engine = criar_engine(caminho)
    with engine.begin() as conexao:
        conexao.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    resposta = _ligar(caminho)

    assert resposta.status_code == 200
    assert "Construtora Alvorada" in resposta.text
    engine = criar_engine(caminho)
    assert revisao_atual(engine) == revisao_mais_recente()
    engine.dispose()

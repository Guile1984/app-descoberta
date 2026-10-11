"""Fixtures do relatório: o banco de demonstração (caso Roberto) e uma sessão vazia."""

from datetime import UTC, date, datetime

import pytest
from sqlmodel import Session

from descoberta.demo import popular_demo
from descoberta.relatorio import Emissao, coletar_dados
from descoberta.repositorio import (
    TipoVersao,
    criar_cliente,
    criar_engine,
    criar_sessao,
    criar_tabelas,
)

EMITIDO_EM = datetime(2026, 10, 11, 17, 5, tzinfo=UTC)


@pytest.fixture
def banco_roberto(tmp_path):
    caminho = tmp_path / "demo.db"
    sessao_id = popular_demo(caminho)
    engine = criar_engine(caminho)
    with Session(engine) as session:
        yield session, sessao_id
    engine.dispose()


@pytest.fixture
def dados_roberto(banco_roberto, questionario_v1):
    session, sessao_id = banco_roberto
    return coletar_dados(session, sessao_id, questionario_v1)


@pytest.fixture
def dados_vazios(tmp_path, questionario_v1):
    engine = criar_engine(tmp_path / "vazio.db")
    criar_tabelas(engine)
    with Session(engine) as session:
        cliente = criar_cliente(session, nome="Ana", empresa="Padaria Sol")
        sessao = criar_sessao(
            session, cliente_id=cliente.id, data=date(2026, 10, 9), versao_questionario=1
        )
        yield coletar_dados(session, sessao.id, questionario_v1)
    engine.dispose()


@pytest.fixture
def emissao_cliente():
    return Emissao(TipoVersao.cliente, numero=None, emitido_em=EMITIDO_EM)


@pytest.fixture
def emissao_interna():
    return Emissao(TipoVersao.interna, numero=None, emitido_em=EMITIDO_EM)

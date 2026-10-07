"""Fixtures dos testes de persistência: cada teste ganha um banco SQLite novo e temporário."""

from datetime import date

import pytest
from sqlmodel import Session

from descoberta.repositorio import criar_cliente, criar_engine, criar_sessao, criar_tabelas


@pytest.fixture
def engine(tmp_path):
    # Arquivo de verdade (não banco em memória), numa pasta temporária que o pytest cria
    # para cada teste: assim testamos o mesmo caminho que a app usa.
    engine = criar_engine(tmp_path / "teste.db")
    criar_tabelas(engine)
    yield engine
    engine.dispose()  # fecha as conexões; no Windows, arquivo aberto não pode ser apagado


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def cliente(session):
    return criar_cliente(
        session,
        nome="Roberto",
        empresa="Construtora Alvorada",
        setor="Construção civil",
        num_funcionarios=40,
        contato="roberto@alvorada.example",
    )


@pytest.fixture
def sessao(session, cliente):
    return criar_sessao(
        session, cliente_id=cliente.id, data=date(2026, 10, 7), versao_questionario=1
    )

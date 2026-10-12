"""Fixtures dos testes do LLM: o caso Roberto do demo, lido do banco."""

from datetime import date
from pathlib import Path

import pytest
from sqlmodel import Session

from descoberta.demo import popular_demo
from descoberta.llm.prompts import carregar_prompts
from descoberta.proposta import carregar_modelo_proposta
from descoberta.relatorio import coletar_dados
from descoberta.relatorio.dados_proposta import coletar_dados_proposta
from descoberta.repositorio import criar_engine

RAIZ = Path(__file__).resolve().parents[2]


@pytest.fixture
def banco_roberto(tmp_path):
    caminho = tmp_path / "demo.db"
    sessao_id = popular_demo(caminho, hoje=date(2026, 10, 11))
    engine = criar_engine(caminho)
    with Session(engine) as session:
        yield session, sessao_id
    engine.dispose()


@pytest.fixture
def dados_roberto(banco_roberto, questionario_v1):
    session, sessao_id = banco_roberto
    return coletar_dados(session, sessao_id, questionario_v1)


@pytest.fixture
def proposta_roberto(banco_roberto, questionario_v1):
    session, sessao_id = banco_roberto
    modelo = carregar_modelo_proposta(RAIZ / "config" / "proposta_v1.yaml")
    return coletar_dados_proposta(session, sessao_id, questionario_v1, modelo)


@pytest.fixture
def prompts():
    return carregar_prompts(RAIZ / "prompts")

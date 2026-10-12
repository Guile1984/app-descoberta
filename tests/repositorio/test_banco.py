from datetime import date, timedelta

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from descoberta.repositorio import (
    Sessao,
    criar_cliente,
    criar_engine,
    criar_tabelas,
    listar_clientes,
)

TABELAS = {
    "cliente",
    "sessao",
    "resposta",
    "sinal_marcado",
    "anotacao",
    "metricas",
    "nota_criterio",
    "relatorio",
    "cronometro",
    # Sprint 6a: saídas da revisão pós-sessão.
    "risco",
    "indicador",
    "item_escopo",
    "proximo_passo",
    "texto_secao",
    # Sprint 6b: relatório.
    "hipotese_metrica",
    "versao_relatorio",
    "perfil_consultor",
    "proposta",
    "fase_proposta",
    "item_proposta",
    "clausula_proposta",
    "versao_proposta",
}


def test_cria_todas_as_tabelas(engine):
    assert set(inspect(engine).get_table_names()) == TABELAS


def test_banco_antigo_ganha_a_tabela_do_cronometro(tmp_path):
    # Bancos criados antes do Sprint 5 (como o data/demo.db) não têm a tabela cronometro.
    # O create_all cria a tabela que falta sem mexer nas outras: não precisa de migração.
    engine = criar_engine(tmp_path / "antigo.db")
    tabelas_antigas = [t for t in SQLModel.metadata.sorted_tables if t.name != "cronometro"]
    SQLModel.metadata.create_all(engine, tables=tabelas_antigas)
    assert "cronometro" not in inspect(engine).get_table_names()
    criar_tabelas(engine)
    assert set(inspect(engine).get_table_names()) == TABELAS
    engine.dispose()


def test_cria_a_pasta_do_banco_se_nao_existir(tmp_path):
    caminho = tmp_path / "pasta" / "nova" / "descoberta.db"
    engine = criar_engine(caminho)
    criar_tabelas(engine)
    engine.dispose()
    assert caminho.exists()


def test_criar_tabelas_duas_vezes_nao_apaga_dados(engine, cliente):
    criar_tabelas(engine)
    with Session(engine) as nova:
        assert [c.nome for c in listar_clientes(nova)] == ["Roberto"]


def test_chaves_estrangeiras_ligadas(session):
    # Inserção direta, sem passar pelas funções do repositório (que já conferem o cliente):
    # quem barra aqui é o próprio SQLite, graças ao PRAGMA foreign_keys=ON.
    session.add(Sessao(cliente_id=999, data=date(2026, 10, 7), versao_questionario=1))
    with pytest.raises(IntegrityError):
        session.commit()


def test_dados_persistem_ao_reabrir_o_banco(tmp_path):
    caminho = tmp_path / "descoberta.db"
    engine = criar_engine(caminho)
    criar_tabelas(engine)
    with Session(engine) as session:
        criar_cliente(session, nome="Roberto", empresa="Construtora Alvorada")
    engine.dispose()

    reaberto = criar_engine(caminho)
    with Session(reaberto) as session:
        assert [c.empresa for c in listar_clientes(session)] == ["Construtora Alvorada"]
    reaberto.dispose()


def test_horarios_voltam_com_fuso_utc(engine, cliente):
    # Horários são gravados em UTC; a tela converte para a hora local ao mostrar.
    with Session(engine) as nova:
        criado_em = listar_clientes(nova)[0].criado_em
    assert criado_em.utcoffset() == timedelta(0)

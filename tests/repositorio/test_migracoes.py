"""Migrações do banco com Alembic.

A app aplica as migrações ao ligar (`migrar`). Três situações:
- banco novo ou vazio: as migrações criam todas as tabelas;
- banco já migrado: só as migrações que faltam rodam (nenhuma, se estiver em dia);
- banco "legado", criado antes do Alembic (como o data/demo.db): se o esquema bate com a
  versão inicial, ele é reconhecido sem tocar nos dados; se não bate, nada é alterado.
"""

import shutil
import sqlite3
from datetime import date
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel

from descoberta.demo import popular_demo
from descoberta.repositorio import (
    REVISAO_INICIAL,
    EsquemaDivergente,
    FalhaNaMigracao,
    criar_cliente,
    criar_engine,
    criar_tabelas,
    listar_clientes,
    migrar,
    revisao_atual,
    revisao_mais_recente,
)
from descoberta.repositorio.banco import PASTA_MIGRACOES

TABELAS = {t.name for t in SQLModel.metadata.sorted_tables}


def _contagens(engine) -> dict[str, int]:
    with engine.connect() as conexao:
        return {
            tabela: conexao.execute(text(f'SELECT COUNT(*) FROM "{tabela}"')).scalar_one()  # noqa: S608 (nomes vêm do próprio esquema)
            for tabela in sorted(TABELAS)
        }


def _banco_legado(caminho):
    """Banco no formato de antes do Alembic: o caso Roberto, sem a tabela alembic_version."""
    popular_demo(caminho, hoje=date(2026, 10, 7))
    engine = criar_engine(caminho)
    with engine.begin() as conexao:
        conexao.execute(text("DROP TABLE alembic_version"))
    return engine


def _copias(pasta):
    return sorted(pasta.glob("*.antes-*.db"))


def test_banco_novo_chega_a_versao_mais_recente(tmp_path):
    engine = criar_engine(tmp_path / "novo.db")
    resultado = migrar(engine)
    assert set(inspect(engine).get_table_names()) == TABELAS | {"alembic_version"}
    assert revisao_atual(engine) == revisao_mais_recente()
    assert resultado.antes is None
    assert resultado.depois == revisao_mais_recente()
    assert not resultado.legado
    assert resultado.copia is None  # banco vazio: nada a proteger
    engine.dispose()


def test_migracoes_produzem_o_mesmo_esquema_dos_modelos(tmp_path):
    # Teste de "deriva": quem muda um modelo e esquece de criar a migração vê este teste
    # falhar, com a diferença na mensagem. Gerar a migração: ver o README (desenvolvimento).
    engine = criar_engine(tmp_path / "deriva.db")
    migrar(engine)
    with engine.connect() as conexao:
        diferencas = compare_metadata(MigrationContext.configure(conexao), SQLModel.metadata)
    engine.dispose()
    assert diferencas == []


def test_migrar_duas_vezes_nao_muda_nada(tmp_path):
    engine = criar_engine(tmp_path / "duas.db")
    migrar(engine)
    with Session(engine) as session:
        criar_cliente(session, nome="Roberto", empresa="Construtora Alvorada")
    resultado = migrar(engine)
    assert resultado.antes == resultado.depois == revisao_mais_recente()
    assert resultado.copia is None  # nada pendente: não precisa de cópia
    with Session(engine) as session:
        assert [c.nome for c in listar_clientes(session)] == ["Roberto"]
    engine.dispose()


def test_banco_legado_e_reconhecido_sem_perder_dados(tmp_path):
    engine = _banco_legado(tmp_path / "demo.db")
    antes = _contagens(engine)
    assert sum(antes.values()) > 0
    assert "alembic_version" not in inspect(engine).get_table_names()

    resultado = migrar(engine)

    assert resultado.legado
    assert resultado.antes is None
    assert resultado.depois == revisao_mais_recente()
    assert revisao_atual(engine) == revisao_mais_recente()
    assert _contagens(engine) == antes
    with Session(engine) as session:
        assert [c.empresa for c in listar_clientes(session)] == ["Construtora Alvorada"]
    engine.dispose()


def test_banco_legado_ganha_copia_de_seguranca_antes(tmp_path):
    engine = _banco_legado(tmp_path / "demo.db")
    antes = _contagens(engine)

    resultado = migrar(engine)
    engine.dispose()

    assert resultado.copia is not None
    assert _copias(tmp_path) == [resultado.copia]
    # O nome termina em .db: fica fora do Git pelo mesmo .gitignore do banco.
    assert resultado.copia.name.startswith("demo.antes-legado-")
    # A cópia é um banco SQLite íntegro, com os mesmos dados e ainda sem alembic_version.
    copia = criar_engine(resultado.copia)
    assert _contagens(copia) == antes
    assert "alembic_version" not in inspect(copia).get_table_names()
    copia.dispose()


def test_banco_legado_sem_tabela_nova_ganha_a_tabela(tmp_path):
    # Bancos de sprints anteriores podem não ter tabelas criadas depois (ex.: cronometro,
    # do Sprint 5). Como antes do Alembic, a tabela que falta é criada; depois, o banco é
    # reconhecido como versão inicial.
    engine = criar_engine(tmp_path / "antigo.db")
    tabelas_antigas = [t for t in SQLModel.metadata.sorted_tables if t.name != "cronometro"]
    SQLModel.metadata.create_all(engine, tables=tabelas_antigas)
    with Session(engine) as session:
        criar_cliente(session, nome="Roberto", empresa="Construtora Alvorada")

    resultado = migrar(engine)

    assert resultado.legado
    assert "cronometro" in inspect(engine).get_table_names()
    assert revisao_atual(engine) == revisao_mais_recente()
    with Session(engine) as session:
        assert len(listar_clientes(session)) == 1
    engine.dispose()


@pytest.mark.parametrize(
    "alteracao",
    [
        "ALTER TABLE cliente ADD COLUMN apelido VARCHAR",
        "ALTER TABLE cliente DROP COLUMN setor",
        "CREATE TABLE tabela_estranha (id INTEGER PRIMARY KEY)",
    ],
    ids=["coluna-a-mais", "coluna-a-menos", "tabela-desconhecida"],
)
def test_banco_legado_divergente_nao_e_alterado(tmp_path, alteracao):
    caminho = tmp_path / "estranho.db"
    engine = criar_engine(caminho)
    criar_tabelas(engine)
    with engine.begin() as conexao:
        conexao.execute(text(alteracao))
    tabelas_antes = set(inspect(engine).get_table_names())

    with pytest.raises(EsquemaDivergente, match="cliente|tabela_estranha"):
        migrar(engine)

    assert set(inspect(engine).get_table_names()) == tabelas_antes  # sem alembic_version
    assert _copias(tmp_path) == []
    engine.dispose()


def test_chaves_estrangeiras_continuam_ligadas_depois_de_migrar(tmp_path):
    # Durante a migração as chaves estrangeiras são desligadas (o SQLite exige isso para
    # recriar tabelas); a conexão volta ao "pool" e precisa voltar com elas ligadas.
    engine = criar_engine(tmp_path / "fk.db")
    migrar(engine)
    for _ in range(3):  # passa pelas conexões reaproveitadas do pool
        with engine.connect() as conexao:
            assert conexao.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    engine.dispose()


def test_versao_inicial_e_a_primeira_da_cadeia():
    assert REVISAO_INICIAL == "0001"


def test_revisao_atual_de_banco_sem_alembic_e_none(tmp_path):
    caminho = tmp_path / "cru.db"
    sqlite3.connect(caminho).close()
    engine = criar_engine(caminho)
    assert revisao_atual(engine) is None
    engine.dispose()


# --- Migração nova sobre um banco com dados (simulada com uma 0002 só dos testes) ---

_MIGRACAO_0002 = """
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("cliente") as batch_op:
        batch_op.add_column(sa.Column("apelido", sa.String(), nullable=True))
    op.create_table("extra", sa.Column("id", sa.Integer(), primary_key=True))
    {falha}


def downgrade():
    pass
"""


def _pasta_com_0002(tmp_path, falha: str = "") -> Path:
    pasta = tmp_path / "migracoes"
    shutil.copytree(PASTA_MIGRACOES, pasta, ignore=shutil.ignore_patterns("__pycache__"))
    (pasta / "versions" / "0002_teste.py").write_text(
        _MIGRACAO_0002.format(falha=falha), encoding="utf-8"
    )
    return pasta


def _banco_na_versao_inicial(caminho):
    engine = criar_engine(caminho)
    migrar(engine)
    with Session(engine) as session:
        criar_cliente(session, nome="Roberto", empresa="Construtora Alvorada", setor="Obras")
    return engine


def test_migracao_pendente_faz_copia_e_preserva_os_dados(tmp_path):
    engine = _banco_na_versao_inicial(tmp_path / "dados" / "descoberta.db")
    pasta = _pasta_com_0002(tmp_path)

    resultado = migrar(engine, pasta)

    assert (resultado.antes, resultado.depois) == ("0001", "0002")
    assert resultado.copia.name.startswith("descoberta.antes-0001-")
    colunas = {c["name"] for c in inspect(engine).get_columns("cliente")}
    assert "apelido" in colunas
    with Session(engine) as session:
        [cliente] = listar_clientes(session)
    assert (cliente.nome, cliente.setor) == ("Roberto", "Obras")
    engine.dispose()


def test_migracao_que_falha_no_meio_nao_altera_o_banco(tmp_path):
    engine = _banco_na_versao_inicial(tmp_path / "dados" / "descoberta.db")
    pasta = _pasta_com_0002(tmp_path, falha='raise RuntimeError("falha simulada")')

    with pytest.raises(FalhaNaMigracao, match="falha simulada"):
        migrar(engine, pasta)

    # A coluna e a tabela criadas antes do erro foram desfeitas: tudo ou nada.
    assert revisao_atual(engine) == "0001"
    assert "extra" not in inspect(engine).get_table_names()
    assert "apelido" not in {c["name"] for c in inspect(engine).get_columns("cliente")}
    with Session(engine) as session:
        assert [c.nome for c in listar_clientes(session)] == ["Roberto"]
    assert len(_copias(tmp_path / "dados")) == 1  # a cópia de antes continua lá
    with engine.connect() as conexao:
        assert conexao.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    engine.dispose()

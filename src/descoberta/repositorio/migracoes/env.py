"""Ambiente das migrações do Alembic.

Dois jeitos de chegar aqui:
- pela app (`repositorio.banco.migrar`), que passa a conexão já aberta em
  `config.attributes["conexao"]`;
- pela linha de comando de quem desenvolve (`uv run alembic revision --autogenerate`),
  que usa o banco de `alembic.ini` (ou da variável DESCOBERTA_BANCO).
"""

import os

from alembic import context
from sqlmodel import SQLModel

from descoberta.repositorio import modelos  # noqa: F401  (registra as tabelas)
from descoberta.repositorio.banco import criar_engine

config = context.config


def _rodar(conexao) -> None:
    context.configure(
        connection=conexao,
        target_metadata=SQLModel.metadata,
        # O SQLite quase não sabe alterar tabelas (ALTER TABLE). No modo "batch", o Alembic
        # cria a tabela nova, copia os dados e troca uma pela outra.
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


conexao = config.attributes.get("conexao")
if conexao is not None:
    _rodar(conexao)
else:
    engine = criar_engine(os.environ.get("DESCOBERTA_BANCO") or config.get_main_option("banco"))
    with engine.connect() as nova:
        _rodar(nova)
    engine.dispose()

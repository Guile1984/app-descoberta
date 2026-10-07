"""Conexão com o arquivo SQLite e criação das tabelas."""

from pathlib import Path

from sqlalchemy import Engine, event
from sqlmodel import SQLModel, create_engine

from . import modelos  # noqa: F401  (registra as tabelas no SQLModel.metadata)

# A pasta data/ está no .gitignore: os dados dos clientes nunca vão para o Git (LGPD).
CAMINHO_BANCO_PADRAO = Path("data") / "descoberta.db"


def criar_engine(caminho: Path | str = CAMINHO_BANCO_PADRAO) -> Engine:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: o FastAPI atende cada pedido numa thread do seu "pool", e
    # a mesma conexão pode passar de uma thread a outra. Cada pedido usa sua própria Session,
    # então não há duas threads mexendo na mesma conexão ao mesmo tempo.
    engine = create_engine(f"sqlite:///{caminho}", connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _ligar_chaves_estrangeiras)
    return engine


def _ligar_chaves_estrangeiras(conexao, _registro) -> None:
    # Por padrão, o SQLite ignora as chaves estrangeiras (aceitaria uma sessão de um cliente
    # que não existe e não apagaria nada em cascata). É preciso ligar em cada conexão.
    cursor = conexao.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def criar_tabelas(engine: Engine) -> None:
    """Cria as tabelas que ainda não existem; não mexe nas que já existem."""
    SQLModel.metadata.create_all(engine)

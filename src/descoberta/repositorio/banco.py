"""Conexão com o arquivo SQLite, criação das tabelas e migrações (Alembic)."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, Engine, MetaData, event, inspect
from sqlmodel import SQLModel, create_engine

from . import modelos  # noqa: F401  (registra as tabelas no SQLModel.metadata)

# A pasta data/ está no .gitignore: os dados dos clientes nunca vão para o Git (LGPD).
CAMINHO_BANCO_PADRAO = Path("data") / "descoberta.db"

PASTA_MIGRACOES = Path(__file__).parent / "migracoes"
# A primeira migração: o esquema de antes do Alembic. Bancos criados antes dela
# ("legados") são reconhecidos comparando o esquema com o desta versão.
REVISAO_INICIAL = "0001"


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
    """Cria as tabelas direto dos modelos, sem migrações (nos testes, por ser mais rápido).

    A app usa `migrar`; o teste de "deriva" garante que os dois caminhos dão o mesmo esquema.
    """
    SQLModel.metadata.create_all(engine)


class EsquemaDivergente(Exception):
    """Banco anterior às migrações cujo esquema não bate com a versão inicial."""


class FalhaNaMigracao(Exception):
    """A migração não terminou; o banco ficou como estava antes dela."""


@dataclass(frozen=True)
class ResultadoMigracao:
    antes: str | None  # revisão antes de migrar (None: banco vazio ou legado)
    depois: str
    legado: bool  # banco de antes do Alembic, reconhecido como versão inicial
    copia: Path | None  # cópia de segurança feita antes de mexer no banco


def migrar(engine: Engine, pasta_migracoes: Path | str = PASTA_MIGRACOES) -> ResultadoMigracao:
    """Leva o banco à versão mais recente. Roda ao ligar a app.

    - banco vazio: cria tudo pelas migrações;
    - banco em dia: não faz nada;
    - banco com migração pendente ou legado: faz uma cópia de segurança ao lado do arquivo
      e depois migra. Um banco legado só é reconhecido se o esquema bater com a versão
      inicial; se não bater, nada é alterado (`EsquemaDivergente`).

    Tudo roda numa transação só: se der erro no meio, o banco volta a como estava
    (`FalhaNaMigracao`), e a cópia continua lá.
    """
    pasta_migracoes = Path(pasta_migracoes)
    mais_recente = revisao_mais_recente(pasta_migracoes)
    tem_dados = bool(_tabelas(engine))
    antes = revisao_atual(engine)
    legado = tem_dados and antes is None

    if legado:
        faltando = _conferir_legado(engine, pasta_migracoes)
    elif antes == mais_recente:
        return ResultadoMigracao(antes, mais_recente, legado=False, copia=None)

    copia = _copiar(engine, antes) if tem_dados else None
    with _ConexaoDeMigracao(engine) as conexao:
        try:
            if legado:
                # Tabelas criadas em sprints posteriores ao banco (antes do Alembic, o
                # create_all criava as que faltavam): criadas agora, como na versão inicial.
                faltando.create_all(conexao)
                command.stamp(_config(pasta_migracoes, conexao), REVISAO_INICIAL)
            command.upgrade(_config(pasta_migracoes, conexao), "head")
            quebradas = conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
            if quebradas:
                raise FalhaNaMigracao(f"referências quebradas depois de migrar: {quebradas[:5]}")
            conexao.exec_driver_sql("COMMIT")
        except Exception as erro:
            conexao.exec_driver_sql("ROLLBACK")
            if isinstance(erro, FalhaNaMigracao):
                raise
            raise FalhaNaMigracao(f"a migração falhou e o banco não foi alterado: {erro}") from erro
    return ResultadoMigracao(antes, revisao_atual(engine), legado=legado, copia=copia)


def revisao_atual(engine: Engine) -> str | None:
    with engine.connect() as conexao:
        return MigrationContext.configure(conexao).get_current_revision()


def revisao_mais_recente(pasta_migracoes: Path | str = PASTA_MIGRACOES) -> str:
    return ScriptDirectory.from_config(_config(Path(pasta_migracoes))).get_current_head()


def _config(pasta_migracoes: Path, conexao: Connection | None = None) -> Config:
    config = Config()
    config.set_main_option("script_location", str(pasta_migracoes))
    config.attributes["conexao"] = conexao
    return config


def _tabelas(engine: Engine) -> set[str]:
    return {t for t in inspect(engine).get_table_names() if t != "alembic_version"}


def _esquema(engine: Engine) -> dict[str, set[str]]:
    inspetor = inspect(engine)
    return {
        tabela: {coluna["name"] for coluna in inspetor.get_columns(tabela)}
        for tabela in inspetor.get_table_names()
        if tabela != "alembic_version"
    }


def _conferir_legado(engine: Engine, pasta_migracoes: Path) -> MetaData:
    """Compara o banco legado com a versão inicial; devolve as tabelas que faltam nele.

    A versão inicial é montada num banco em memória, rodando a migração 0001 de verdade:
    assim a comparação nunca depende dos modelos atuais, que vão mudar com o tempo.
    """
    referencia = create_engine("sqlite://")
    try:
        with referencia.begin() as conexao:
            command.upgrade(_config(pasta_migracoes, conexao), REVISAO_INICIAL)
        esperado = _esquema(referencia)
        encontrado = _esquema(engine)

        diferencas = [
            f"tabela desconhecida {t}" for t in sorted(encontrado.keys() - esperado.keys())
        ]
        for tabela in sorted(encontrado.keys() & esperado.keys()):
            if sobra := encontrado[tabela] - esperado[tabela]:
                diferencas.append(f"{tabela}: colunas a mais {sorted(sobra)}")
            if falta := esperado[tabela] - encontrado[tabela]:
                diferencas.append(f"{tabela}: colunas a menos {sorted(falta)}")
        if diferencas:
            raise EsquemaDivergente(
                "o banco é anterior às migrações, mas o esquema não bate com a versão "
                "inicial; nada foi alterado. Diferenças: " + "; ".join(diferencas)
            )

        faltando = MetaData()
        faltando.reflect(referencia, only=sorted(esperado.keys() - encontrado.keys()))
        return faltando
    finally:
        referencia.dispose()


def _copiar(engine: Engine, revisao: str | None) -> Path:
    """Cópia de segurança com a API de backup do SQLite (íntegra mesmo com a app aberta).

    O nome termina em .db, então fica fora do Git pelo mesmo .gitignore do banco.
    """
    original = Path(engine.url.database)
    agora = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = original.with_name(f"{original.stem}.antes-{revisao or 'legado'}-{agora}.db")
    copia = sqlite3.connect(destino)
    try:
        with engine.connect() as conexao:
            conexao.connection.driver_connection.backup(copia)
    finally:
        copia.close()
    return destino


class _ConexaoDeMigracao:
    """Conexão preparada para migrar o SQLite com segurança.

    - Chaves estrangeiras desligadas: para alterar uma tabela, o SQLite cria outra, copia
      os dados e apaga a antiga; com as chaves ligadas, apagar a antiga apagaria em
      cascata os registros que apontam para ela. No fim, `foreign_key_check` confere tudo.
    - Transação de verdade: por padrão, o driver do Python grava cada CREATE/ALTER na hora;
      aqui ele fica em modo manual e a migração inteira vai entre BEGIN e COMMIT.
    A conexão volta ao "pool" como estava (chaves ligadas, modo padrão do driver).
    """

    def __init__(self, engine: Engine) -> None:
        self._conexao = engine.connect()

    def __enter__(self) -> Connection:
        driver = self._conexao.connection.driver_connection
        self._modo = driver.isolation_level
        driver.isolation_level = None
        self._conexao.exec_driver_sql("PRAGMA foreign_keys=OFF")
        self._conexao.exec_driver_sql("BEGIN")
        return self._conexao

    def __exit__(self, *_erro) -> None:
        driver = self._conexao.connection.driver_connection
        self._conexao.exec_driver_sql("PRAGMA foreign_keys=ON")
        driver.isolation_level = self._modo
        self._conexao.close()

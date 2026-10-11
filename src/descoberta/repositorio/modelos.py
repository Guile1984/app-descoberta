"""Tabelas do banco (SQLModel).

Os ids que vêm do questionário (pergunta, sinal, critério, tipo de solução) são guardados
como texto, exatamente como estão no YAML ("b2.s3"). O catálogo não vira tabela: ele vive
no YAML, e cada sessão registra a versão do questionário usada.

Atenção: modelos com `table=True` NÃO validam os dados ao serem criados (o SQLModel pula
a validação do Pydantic). Por isso a validação fica nas funções do repositório.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum, auto
from typing import Any

from sqlalchemy import LargeBinary, UniqueConstraint
from sqlmodel import Field, SQLModel

from descoberta.dominio.revisao import Camada, Nivel, Responsavel

from .tipos import DecimalTexto


class StatusSessao(StrEnum):
    # auto() num StrEnum usa o próprio nome como valor: o banco guarda "em_andamento".
    preparacao = auto()
    em_andamento = auto()
    concluida = auto()


class TipoVersao(StrEnum):
    """Para quem é a versão do relatório: a interna tem sinais de alerta e anotações."""

    cliente = auto()
    interna = auto()


class OrigemRelatorio(StrEnum):
    template = auto()
    llm = auto()


def agora() -> datetime:
    # Horários com fuso, em UTC: é o padrão do SQLModel, e a tela converte para a hora
    # local na hora de mostrar (datetime.astimezone()).
    return datetime.now(UTC)


def _id_da_sessao() -> Any:
    # ondelete="CASCADE": excluir a sessão apaga junto tudo o que pertence a ela.
    return Field(foreign_key="sessao.id", ondelete="CASCADE", index=True)


def _dinheiro_ou_quantidade() -> Any:
    return Field(default=None, sa_type=DecimalTexto)


class Cliente(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str
    empresa: str
    setor: str | None = None
    num_funcionarios: int | None = None
    contato: str | None = None
    criado_em: datetime = Field(default_factory=agora)


class Sessao(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", ondelete="CASCADE", index=True)
    data: date
    versao_questionario: int
    tipo_solucao: str | None = None  # id do YAML; define as perguntas condicionais
    status: StatusSessao = StatusSessao.preparacao
    contexto_previo: str | None = None
    amostra_dados_recebida: bool = False
    criado_em: datetime = Field(default_factory=agora)


class Resposta(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("sessao_id", "pergunta_id"),)

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    pergunta_id: str
    texto: str
    atualizado_em: datetime = Field(default_factory=agora)


class SinalMarcado(SQLModel, table=True):
    __tablename__ = "sinal_marcado"
    __table_args__ = (UniqueConstraint("sessao_id", "sinal_id"),)

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    sinal_id: str
    observacao: str | None = None
    marcado_em: datetime = Field(default_factory=agora)


class Anotacao(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    bloco: int | None = None  # anotação geral quando não está ligada a um bloco
    texto: str
    criado_em: datetime = Field(default_factory=agora)


class Metricas(SQLModel, table=True):
    """Números da sessão, cada um no seu campo (nunca extraídos do texto das respostas).

    Os nomes são os mesmos parâmetros das funções de `dominio`. Todos são opcionais
    porque vão sendo preenchidos ao longo da conversa.
    """

    # Uma linha por sessão: o id da sessão é a própria chave.
    sessao_id: int = Field(primary_key=True, foreign_key="sessao.id", ondelete="CASCADE")
    # Bloco 1 — custo da dor.
    horas_por_ocorrencia: Decimal | None = _dinheiro_ou_quantidade()
    frequencia_quantidade: Decimal | None = _dinheiro_ou_quantidade()
    frequencia_periodo: str | None = None  # "dia", "semana" ou "mes"
    custo_hora: Decimal | None = _dinheiro_ou_quantidade()
    # Bloco 9 — retorno.
    horas_economizadas_mes: Decimal | None = _dinheiro_ou_quantidade()
    outros_ganhos_mes: Decimal | None = _dinheiro_ou_quantidade()
    investimento: Decimal | None = _dinheiro_ou_quantidade()
    # Bloco 6 — custo de operação.
    chamadas_por_dia: Decimal | None = _dinheiro_ou_quantidade()
    custo_por_chamada: Decimal | None = _dinheiro_ou_quantidade()
    custo_fixo_mes: Decimal | None = _dinheiro_ou_quantidade()


class Cronometro(SQLModel, table=True):
    """Tempo da sessão: soma dos trechos já pausados mais o trecho que está rodando.

    Tabela própria (e não colunas novas em Sessao) porque o create_all cria tabelas novas
    num banco que já existe, mas não acrescenta colunas às antigas.
    """

    sessao_id: int = Field(primary_key=True, foreign_key="sessao.id", ondelete="CASCADE")
    acumulado_segundos: int = 0
    rodando_desde: datetime | None = None  # None: pausado (ou nunca iniciado)


class NotaCriterio(SQLModel, table=True):
    """Nota 0–3 de um critério de score (os ids de critério são únicos no questionário)."""

    __tablename__ = "nota_criterio"
    __table_args__ = (UniqueConstraint("sessao_id", "criterio_id"),)

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    criterio_id: str
    nota: int


class Relatorio(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    origem: OrigemRelatorio
    conteudo: str
    modelo: str | None = None  # modelo de LLM usado (só quando origem = llm)
    versao_prompt: str | None = None
    criado_em: datetime = Field(default_factory=agora)


# --- Revisão pós-sessão (Sprint 6a) ---
# Tabelas novas, e não colunas em tabelas antigas: o create_all cria as tabelas num banco
# que já existe (como o data/demo.db), sem precisar de migração.


class Risco(SQLModel, table=True):
    """Uma linha da matriz de riscos do bloco 7."""

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    descricao: str
    categoria: str  # id do YAML (revisao.categorias_risco)
    probabilidade: Nivel
    impacto: Nivel
    mitigacao: str | None = None
    criado_em: datetime = Field(default_factory=agora)


class Indicador(SQLModel, table=True):
    """Uma linha da tabela "indicador atual → meta → prazo → como medir" do bloco 5.

    Valor atual, meta e prazo são texto ("Recall ≥ 95%", "3 dias", "fim do piloto"):
    misturam unidades e não entram em nenhum cálculo.
    """

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    nome: str
    camada: Camada
    valor_atual: str | None = None
    meta: str | None = None
    prazo: str | None = None
    como_medir: str | None = None
    criado_em: datetime = Field(default_factory=agora)


class ItemEscopo(SQLModel, table=True):
    """Item do escopo do MVP: o que entra (entra=True) e o que fica de fora."""

    __tablename__ = "item_escopo"

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    texto: str
    entra: bool
    criado_em: datetime = Field(default_factory=agora)


class ProximoPasso(SQLModel, table=True):
    __tablename__ = "proximo_passo"

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    acao: str
    responsavel: Responsavel
    prazo: date | None = None
    criado_em: datetime = Field(default_factory=agora)


class TextoSecao(SQLModel, table=True):
    """Texto de uma parte narrativa do relatório (ids em revisao.textos do YAML)."""

    __tablename__ = "texto_secao"
    __table_args__ = (UniqueConstraint("sessao_id", "secao_id"),)

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    secao_id: str
    texto: str
    atualizado_em: datetime = Field(default_factory=agora)


# --- Relatório (Sprint 6b) ---


class HipoteseMetrica(SQLModel, table=True):
    """Métrica que o consultor assumiu (não foi dita pelo cliente): o relatório a destaca."""

    __tablename__ = "hipotese_metrica"
    __table_args__ = (UniqueConstraint("sessao_id", "campo"),)

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    campo: str  # nome do campo em Metricas (ex.: "custo_hora")


class VersaoRelatorio(SQLModel, table=True):
    """PDF do relatório registrado como enviado, guardado exatamente como foi emitido.

    Dois hashes SHA-256: o do conteúdo (o texto do relatório em Markdown), impresso no
    rodapé de cada página, e o do arquivo PDF. Um arquivo não pode conter o próprio hash
    (imprimi-lo mudaria o arquivo), por isso o rodapé leva o hash do conteúdo.
    """

    __tablename__ = "versao_relatorio"
    __table_args__ = (UniqueConstraint("sessao_id", "numero"),)

    id: int | None = Field(default=None, primary_key=True)
    sessao_id: int = _id_da_sessao()
    numero: int  # 1, 2, 3… em cada sessão
    tipo: TipoVersao
    emitido_em: datetime
    conteudo_md: str
    hash_conteudo: str
    pdf: bytes = Field(sa_type=LargeBinary)
    hash_pdf: str

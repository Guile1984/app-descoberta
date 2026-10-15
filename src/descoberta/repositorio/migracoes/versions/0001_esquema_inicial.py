"""Esquema inicial: o banco como estava no fim do Sprint 7 (versão 0.10.0).

Gerada pelo autogenerate e revisada. Bancos criados antes do Alembic (como o data/demo.db)
não passam por aqui: `repositorio.banco.migrar` confere que o esquema deles é igual ao
desta versão e só a registra (stamp), sem tocar nos dados.

Revisão: 0001
Anterior: nenhuma
Criada em: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

import descoberta.repositorio.tipos

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("empresa", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("setor", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("num_funcionarios", sa.Integer(), nullable=True),
        sa.Column("contato", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "perfil_consultor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("empresa", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("cpf_cnpj", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("telefone", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("cidade", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("uf", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("logotipo", sa.LargeBinary(), nullable=True),
        sa.Column("dados_ficticios", sa.Boolean(), nullable=False),
        sa.Column("atualizado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sessao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("versao_questionario", sa.Integer(), nullable=False),
        sa.Column("tipo_solucao", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("preparacao", "em_andamento", "concluida", name="statussessao"),
            nullable=False,
        ),
        sa.Column("contexto_previo", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("amostra_dados_recebida", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("sessao", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_sessao_cliente_id"), ["cliente_id"], unique=False)

    op.create_table(
        "anotacao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("bloco", sa.Integer(), nullable=True),
        sa.Column("texto", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("anotacao", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_anotacao_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "clausula_proposta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("clausula_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("texto", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("excluida", sa.Boolean(), nullable=False),
        sa.Column("atualizado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "clausula_id"),
    )
    with op.batch_alter_table("clausula_proposta", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_clausula_proposta_sessao_id"), ["sessao_id"], unique=False
        )

    op.create_table(
        "cronometro",
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("acumulado_segundos", sa.Integer(), nullable=False),
        sa.Column("rodando_desde", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("sessao_id"),
    )
    op.create_table(
        "fase_proposta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("nome", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("objetivo", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("duracao_semanas", sa.Integer(), nullable=True),
        sa.Column("investimento", descoberta.repositorio.tipos.DecimalTexto(), nullable=True),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("fase_proposta", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_fase_proposta_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "hipotese_metrica",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("campo", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "campo"),
    )
    with op.batch_alter_table("hipotese_metrica", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_hipotese_metrica_sessao_id"), ["sessao_id"], unique=False
        )

    op.create_table(
        "indicador",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("nome", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("camada", sa.Enum("negocio", "tecnica", name="camada"), nullable=False),
        sa.Column("valor_atual", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("meta", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("prazo", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("como_medir", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("indicador", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_indicador_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "item_escopo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("texto", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("entra", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("item_escopo", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_item_escopo_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "metricas",
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column(
            "horas_por_ocorrencia", descoberta.repositorio.tipos.DecimalTexto(), nullable=True
        ),
        sa.Column(
            "frequencia_quantidade", descoberta.repositorio.tipos.DecimalTexto(), nullable=True
        ),
        sa.Column("frequencia_periodo", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("custo_hora", descoberta.repositorio.tipos.DecimalTexto(), nullable=True),
        sa.Column(
            "horas_economizadas_mes", descoberta.repositorio.tipos.DecimalTexto(), nullable=True
        ),
        sa.Column("outros_ganhos_mes", descoberta.repositorio.tipos.DecimalTexto(), nullable=True),
        sa.Column("investimento", descoberta.repositorio.tipos.DecimalTexto(), nullable=True),
        sa.Column("chamadas_por_dia", descoberta.repositorio.tipos.DecimalTexto(), nullable=True),
        sa.Column("custo_por_chamada", descoberta.repositorio.tipos.DecimalTexto(), nullable=True),
        sa.Column("custo_fixo_mes", descoberta.repositorio.tipos.DecimalTexto(), nullable=True),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("sessao_id"),
    )
    op.create_table(
        "nota_criterio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("criterio_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("nota", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "criterio_id"),
    )
    with op.batch_alter_table("nota_criterio", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_nota_criterio_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "pessoa_citada",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("nome", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("pessoa_citada", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_pessoa_citada_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "previa_llm",
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("impressao", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("confirmada_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("sessao_id"),
    )
    op.create_table(
        "proposta",
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("versao_modelo", sa.Integer(), nullable=False),
        sa.Column("cliente_cpf_cnpj", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("cliente_representante", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("cliente_cargo", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("cliente_email", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("cliente_cidade", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("cliente_uf", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("condicoes_pagamento", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("impostos", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("reajuste", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("validade_dias", sa.Integer(), nullable=False),
        sa.Column("criada_com_alerta", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("sessao_id"),
    )
    op.create_table(
        "proximo_passo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("acao", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "responsavel", sa.Enum("cliente", "consultor", name="responsavel"), nullable=False
        ),
        sa.Column("prazo", sa.Date(), nullable=True),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("proximo_passo", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_proximo_passo_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "rascunho",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column(
            "destino", sa.Enum("revisao", "proposta", name="destinorascunho"), nullable=False
        ),
        sa.Column("campo", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("texto", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("provedor", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("modelo", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("versao_prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("alertas", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("com_anotacoes_internas", sa.Boolean(), nullable=False),
        sa.Column(
            "situacao",
            sa.Enum("pendente", "aceito", "descartado", "substituido", name="situacaorascunho"),
            nullable=False,
        ),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column("decidido_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("rascunho", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_rascunho_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "relatorio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("origem", sa.Enum("template", "llm", name="origemrelatorio"), nullable=False),
        sa.Column("conteudo", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("modelo", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("versao_prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("relatorio", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_relatorio_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "resposta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("pergunta_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("texto", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("atualizado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "pergunta_id"),
    )
    with op.batch_alter_table("resposta", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_resposta_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "risco",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("categoria", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("probabilidade", sa.Enum("baixo", "medio", "alto", name="nivel"), nullable=False),
        sa.Column("impacto", sa.Enum("baixo", "medio", "alto", name="nivel"), nullable=False),
        sa.Column("mitigacao", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("risco", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_risco_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "sinal_marcado",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("sinal_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("observacao", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("marcado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "sinal_id"),
    )
    with op.batch_alter_table("sinal_marcado", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_sinal_marcado_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "texto_proposta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("campo", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("texto", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("atualizado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "campo"),
    )
    with op.batch_alter_table("texto_proposta", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_texto_proposta_sessao_id"), ["sessao_id"], unique=False
        )

    op.create_table(
        "texto_secao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("secao_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("texto", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("atualizado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "secao_id"),
    )
    with op.batch_alter_table("texto_secao", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_texto_secao_sessao_id"), ["sessao_id"], unique=False)

    op.create_table(
        "versao_proposta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("emitido_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column("conteudo_md", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("hash_conteudo", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("pdf", sa.LargeBinary(), nullable=False),
        sa.Column("hash_pdf", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("versao_modelo", sa.Integer(), nullable=False),
        sa.Column("clausulas", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "numero"),
    )
    with op.batch_alter_table("versao_proposta", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_versao_proposta_sessao_id"), ["sessao_id"], unique=False
        )

    op.create_table(
        "versao_relatorio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.Enum("cliente", "interna", name="tipoversao"), nullable=False),
        sa.Column("emitido_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.Column("conteudo_md", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("hash_conteudo", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("pdf", sa.LargeBinary(), nullable=False),
        sa.Column("hash_pdf", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sessao_id", "numero"),
    )
    with op.batch_alter_table("versao_relatorio", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_versao_relatorio_sessao_id"), ["sessao_id"], unique=False
        )

    op.create_table(
        "item_proposta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sessao_id", sa.Integer(), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum(
                "escopo",
                "entregavel",
                "exclusao",
                "premissa",
                "responsabilidade",
                name="tipoitemproposta",
            ),
            nullable=False,
        ),
        sa.Column("fase_id", sa.Integer(), nullable=True),
        sa.Column("texto", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("criado_em", sqlmodel.sql.sqltypes.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["fase_id"], ["fase_proposta.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sessao_id"], ["sessao.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("item_proposta", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_item_proposta_fase_id"), ["fase_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_item_proposta_sessao_id"), ["sessao_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("item_proposta", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_item_proposta_sessao_id"))
        batch_op.drop_index(batch_op.f("ix_item_proposta_fase_id"))

    op.drop_table("item_proposta")
    with op.batch_alter_table("versao_relatorio", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_versao_relatorio_sessao_id"))

    op.drop_table("versao_relatorio")
    with op.batch_alter_table("versao_proposta", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_versao_proposta_sessao_id"))

    op.drop_table("versao_proposta")
    with op.batch_alter_table("texto_secao", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_texto_secao_sessao_id"))

    op.drop_table("texto_secao")
    with op.batch_alter_table("texto_proposta", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_texto_proposta_sessao_id"))

    op.drop_table("texto_proposta")
    with op.batch_alter_table("sinal_marcado", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_sinal_marcado_sessao_id"))

    op.drop_table("sinal_marcado")
    with op.batch_alter_table("risco", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_risco_sessao_id"))

    op.drop_table("risco")
    with op.batch_alter_table("resposta", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_resposta_sessao_id"))

    op.drop_table("resposta")
    with op.batch_alter_table("relatorio", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_relatorio_sessao_id"))

    op.drop_table("relatorio")
    with op.batch_alter_table("rascunho", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_rascunho_sessao_id"))

    op.drop_table("rascunho")
    with op.batch_alter_table("proximo_passo", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_proximo_passo_sessao_id"))

    op.drop_table("proximo_passo")
    op.drop_table("proposta")
    op.drop_table("previa_llm")
    with op.batch_alter_table("pessoa_citada", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pessoa_citada_sessao_id"))

    op.drop_table("pessoa_citada")
    with op.batch_alter_table("nota_criterio", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_nota_criterio_sessao_id"))

    op.drop_table("nota_criterio")
    op.drop_table("metricas")
    with op.batch_alter_table("item_escopo", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_item_escopo_sessao_id"))

    op.drop_table("item_escopo")
    with op.batch_alter_table("indicador", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_indicador_sessao_id"))

    op.drop_table("indicador")
    with op.batch_alter_table("hipotese_metrica", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_hipotese_metrica_sessao_id"))

    op.drop_table("hipotese_metrica")
    with op.batch_alter_table("fase_proposta", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_fase_proposta_sessao_id"))

    op.drop_table("fase_proposta")
    op.drop_table("cronometro")
    with op.batch_alter_table("clausula_proposta", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_clausula_proposta_sessao_id"))

    op.drop_table("clausula_proposta")
    with op.batch_alter_table("anotacao", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_anotacao_sessao_id"))

    op.drop_table("anotacao")
    with op.batch_alter_table("sessao", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_sessao_cliente_id"))

    op.drop_table("sessao")
    op.drop_table("perfil_consultor")
    op.drop_table("cliente")

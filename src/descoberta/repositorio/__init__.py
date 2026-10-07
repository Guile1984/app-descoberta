"""Persistência com SQLModel + SQLite.

Cada função recebe a `Session` do SQLModel e grava numa transação própria (faz commit),
combinando com o salvamento automático a cada campo da tela.
"""

from ._comum import RegistroNaoEncontrado
from .banco import CAMINHO_BANCO_PADRAO, criar_engine, criar_tabelas
from .clientes import (
    atualizar_cliente,
    criar_cliente,
    excluir_cliente,
    listar_clientes,
    obter_cliente,
)
from .metricas import notas_da_sessao, obter_metricas, salvar_metricas, salvar_nota
from .modelos import (
    Anotacao,
    Cliente,
    Metricas,
    NotaCriterio,
    OrigemRelatorio,
    Relatorio,
    Resposta,
    Sessao,
    SinalMarcado,
    StatusSessao,
)
from .registros import (
    adicionar_anotacao,
    anotacoes_da_sessao,
    desmarcar_sinal,
    editar_anotacao,
    excluir_anotacao,
    marcar_sinal,
    respostas_da_sessao,
    salvar_resposta,
    sinais_marcados,
)
from .relatorios import listar_relatorios, obter_relatorio, salvar_relatorio
from .sessoes import (
    atualizar_sessao,
    criar_sessao,
    excluir_sessao,
    listar_sessoes,
    obter_sessao,
)

__all__ = [
    "CAMINHO_BANCO_PADRAO",
    "Anotacao",
    "Cliente",
    "Metricas",
    "NotaCriterio",
    "OrigemRelatorio",
    "RegistroNaoEncontrado",
    "Relatorio",
    "Resposta",
    "Sessao",
    "SinalMarcado",
    "StatusSessao",
    "adicionar_anotacao",
    "anotacoes_da_sessao",
    "atualizar_cliente",
    "atualizar_sessao",
    "criar_cliente",
    "criar_engine",
    "criar_sessao",
    "criar_tabelas",
    "desmarcar_sinal",
    "editar_anotacao",
    "excluir_anotacao",
    "excluir_cliente",
    "excluir_sessao",
    "listar_clientes",
    "listar_relatorios",
    "listar_sessoes",
    "marcar_sinal",
    "notas_da_sessao",
    "obter_cliente",
    "obter_metricas",
    "obter_relatorio",
    "obter_sessao",
    "respostas_da_sessao",
    "salvar_metricas",
    "salvar_nota",
    "salvar_relatorio",
    "salvar_resposta",
    "sinais_marcados",
]

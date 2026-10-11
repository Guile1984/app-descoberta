"""Relatório de Descoberta: montagem (versão cliente e interna) e exportação.

dados = coletar_dados(session, sessao_id, questionario)
emitido = emitir(dados, Emissao(TipoVersao.cliente, numero=None, emitido_em=agora()))
exportar_pdf(emitido)  # ou exportar_docx, exportar_markdown
"""

from .dados import DadosRelatorio, coletar_dados
from .emissao import RelatorioEmitido, emitir
from .exportar import exportar_docx, exportar_markdown, exportar_pdf
from .montagem import Emissao, montar_relatorio

__all__ = [
    "DadosRelatorio",
    "Emissao",
    "RelatorioEmitido",
    "coletar_dados",
    "emitir",
    "exportar_docx",
    "exportar_markdown",
    "exportar_pdf",
    "montar_relatorio",
]

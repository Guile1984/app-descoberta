"""Relatório de Descoberta: montagem (versão cliente e interna) e exportação.

dados = coletar_dados(session, sessao_id, questionario)
emitido = emitir(dados, Emissao(TipoVersao.cliente, numero=None, emitido_em=agora()))
exportar_pdf(emitido)  # ou exportar_docx, exportar_markdown
"""

from .dados import DadosRelatorio, coletar_dados
from .dados_proposta import DadosProposta, coletar_dados_proposta, dados_para_proposta_nova
from .emissao import PropostaEmitida, RelatorioEmitido, emitir, emitir_proposta
from .exportar import exportar_docx, exportar_markdown, exportar_pdf
from .montagem import Emissao, montar_relatorio
from .proposta import EmissaoProposta, montar_proposta

__all__ = [
    "DadosProposta",
    "DadosRelatorio",
    "Emissao",
    "EmissaoProposta",
    "PropostaEmitida",
    "RelatorioEmitido",
    "coletar_dados",
    "coletar_dados_proposta",
    "dados_para_proposta_nova",
    "emitir",
    "emitir_proposta",
    "exportar_docx",
    "exportar_markdown",
    "exportar_pdf",
    "montar_proposta",
    "montar_relatorio",
]

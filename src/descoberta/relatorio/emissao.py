"""Emissão do relatório: documento montado, texto canônico, hash e rodapé.

O hash impresso no rodapé é o SHA-256 do texto canônico do relatório (o Markdown gerado
do documento). Ele não pode ser o hash do próprio PDF: imprimir o hash dentro do arquivo
mudaria o arquivo, e o hash deixaria de valer. Para conferir uma cópia assinada, compare o
número da versão e o começo do hash do rodapé com a versão registrada na app.
"""

from dataclasses import dataclass

from descoberta.repositorio import TipoVersao, hash_do_conteudo

from .dados import DadosRelatorio
from .dados_proposta import DadosProposta
from .documento import Documento
from .exportar.markdown import markdown_do_documento
from .montagem import Emissao, descricao_da_emissao, montar_relatorio
from .proposta import EmissaoProposta, descricao_da_emissao_proposta, montar_proposta

CARACTERES_DO_HASH = 12  # quantos caracteres do hash aparecem no rodapé


@dataclass(frozen=True)
class RelatorioEmitido:
    emissao: Emissao
    documento: Documento
    markdown: str  # texto canônico: é dele o hash
    hash_conteudo: str

    @property
    def rodape(self) -> str:
        """Texto do rodapé de cada página (o número da página é acrescentado no PDF/DOCX)."""
        prefixo = "USO INTERNO · " if self.emissao.tipo == TipoVersao.interna else ""
        resumo = self.hash_conteudo[:CARACTERES_DO_HASH]
        return f"{prefixo}{descricao_da_emissao(self.emissao)} · hash {resumo}"


def emitir(dados: DadosRelatorio, emissao: Emissao) -> RelatorioEmitido:
    documento = montar_relatorio(dados, emissao)
    markdown = markdown_do_documento(documento)
    return RelatorioEmitido(emissao, documento, markdown, hash_do_conteudo(markdown))


@dataclass(frozen=True)
class PropostaEmitida:
    """A proposta emitida: mesmo esquema do relatório (texto canônico, hash e rodapé)."""

    emissao: EmissaoProposta
    documento: Documento
    markdown: str
    hash_conteudo: str

    @property
    def rodape(self) -> str:
        resumo = self.hash_conteudo[:CARACTERES_DO_HASH]
        return f"Proposta · {descricao_da_emissao_proposta(self.emissao)} · hash {resumo}"


def emitir_proposta(dados: DadosProposta, emissao: EmissaoProposta) -> PropostaEmitida:
    documento = montar_proposta(dados, emissao)
    markdown = markdown_do_documento(documento)
    return PropostaEmitida(emissao, documento, markdown, hash_do_conteudo(markdown))

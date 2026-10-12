"""Relatório de Descoberta: prévia, downloads e versões registradas como enviadas.

- Prévia e downloads geram o relatório na hora, com os dados atuais, como rascunho
  ("Rascunho não registrado" no rodapé). Nada é gravado.
- "Registrar versão enviada" gera o PDF com o próximo número de versão e o guarda no
  banco, com os hashes. O download de uma versão registrada devolve o PDF guardado,
  byte a byte, mesmo que os dados da sessão mudem depois.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import Response
from sqlmodel import Session

from descoberta.formatos import slug
from descoberta.questionario import Questionario
from descoberta.relatorio import (
    DadosRelatorio,
    Emissao,
    coletar_dados,
    emitir,
    exportar_docx,
    exportar_markdown,
    exportar_pdf,
)
from descoberta.relatorio.documento import FALTA
from descoberta.repositorio import (
    Sessao,
    TipoVersao,
    obter_cliente,
    obter_versao,
    proximo_numero_versao,
    registrar_versao,
    versoes_da_sessao,
)
from descoberta.repositorio.modelos import agora

from ..dependencias import Banco, CatalogoDep, exigir_sessao, html, redirecionar

router = APIRouter()

FORMATOS = {
    "md": ("text/markdown; charset=utf-8", lambda e: exportar_markdown(e).encode("utf-8")),
    "docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        exportar_docx,
    ),
    "pdf": ("application/pdf", exportar_pdf),
}
ROTULOS_VERSAO = {TipoVersao.cliente: "Cliente", TipoVersao.interna: "Interna"}


def _tipo(versao: str) -> TipoVersao:
    try:
        return TipoVersao(versao)
    except ValueError:
        raise HTTPException(404, f"O relatório não tem a versão '{versao}'.") from None


def _dados(banco: Session, sessao: Sessao, questionario: Questionario) -> DadosRelatorio:
    try:
        return coletar_dados(banco, sessao.id, questionario)
    except ValueError as erro:  # dado gravado que o questionário da sessão não reconhece
        raise HTTPException(422, f"Não foi possível montar o relatório: {erro}") from None


def _nome_do_arquivo(
    empresa: str, data: date, tipo: TipoVersao, extensao: str, numero: int | None = None
) -> str:
    """relatorio-descoberta-construtora-alvorada-2026-10-07-cliente-v1.pdf (só ASCII)."""
    sufixo = f"-v{numero}" if numero else ""
    return f"relatorio-descoberta-{slug(empresa)}-{data.isoformat()}-{tipo}{sufixo}.{extensao}"


def arquivo(conteudo: bytes, tipo_conteudo: str, nome: str) -> Response:
    return Response(
        conteudo,
        media_type=tipo_conteudo,
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.get("/sessoes/{sessao_id}/relatorio")
def pagina(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, versao: str = "cliente"
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    tipo = _tipo(versao)
    dados = _dados(banco, sessao, questionario)
    emitido = emitir(dados, Emissao(tipo, numero=None, emitido_em=agora()))
    return html(
        request,
        "relatorio/pagina.html",
        sessao=sessao,
        dados=dados,
        tipo=tipo,
        rotulos_versao=ROTULOS_VERSAO,
        documento=emitido.documento,
        a_preencher=emitido.markdown.count(FALTA),
        versoes=versoes_da_sessao(banco, sessao_id),
    )


@router.get("/sessoes/{sessao_id}/relatorio.{formato}")
def baixar(banco: Banco, catalogo: CatalogoDep, sessao_id: int, formato: str, versao: str):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    if formato not in FORMATOS:
        raise HTTPException(404, f"O relatório não é exportado em '{formato}'.")
    tipo = _tipo(versao)
    dados = _dados(banco, sessao, questionario)
    emitido = emitir(dados, Emissao(tipo, numero=None, emitido_em=agora()))
    tipo_conteudo, exportar = FORMATOS[formato]
    return arquivo(
        exportar(emitido),
        tipo_conteudo,
        _nome_do_arquivo(dados.empresa, dados.data_sessao, tipo, formato),
    )


@router.post("/sessoes/{sessao_id}/relatorio/versoes")
def registrar(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    versao: Annotated[str, Form()] = "",
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    tipo = _tipo(versao)
    dados = _dados(banco, sessao, questionario)
    emissao = Emissao(tipo, numero=proximo_numero_versao(banco, sessao_id), emitido_em=agora())
    emitido = emitir(dados, emissao)
    registrar_versao(
        banco,
        sessao_id,
        numero=emissao.numero,
        tipo=tipo,
        emitido_em=emissao.emitido_em,
        conteudo_md=emitido.markdown,
        pdf=exportar_pdf(emitido),
    )
    # Depois de um POST, redirecionar (padrão "POST → redirecionamento → GET"): o F5 na
    # página seguinte não registra a versão de novo.
    return redirecionar(request, f"/sessoes/{sessao_id}/relatorio?versao={tipo}#versoes")


@router.get("/sessoes/{sessao_id}/relatorio/versoes/{numero}.pdf")
def baixar_versao(banco: Banco, catalogo: CatalogoDep, sessao_id: int, numero: int):
    sessao, _ = exigir_sessao(banco, catalogo, sessao_id)
    versao = obter_versao(banco, sessao_id, numero)
    if versao is None:
        raise HTTPException(404, f"A sessão não tem a versão {numero} registrada.")
    empresa = obter_cliente(banco, sessao.cliente_id).empresa
    nome = _nome_do_arquivo(empresa, sessao.data, versao.tipo, "pdf", numero)
    return arquivo(versao.pdf, "application/pdf", nome)

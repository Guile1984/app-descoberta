"""Anotações livres da sessão: criar (Alt+N, Ctrl+Enter), editar e excluir."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from descoberta.repositorio import (
    Anotacao,
    adicionar_anotacao,
    anotacoes_da_sessao,
    editar_anotacao,
    excluir_anotacao,
)

from ..dependencias import Banco, CatalogoDep, exigir_sessao, html
from ..formularios import inteiro_ou_nada

router = APIRouter()


def _exigir_anotacao(banco: Banco, sessao_id: int, anotacao_id: int) -> Anotacao:
    anotacao = banco.get(Anotacao, anotacao_id)
    if anotacao is None or anotacao.sessao_id != sessao_id:
        raise HTTPException(404, f"Anotação {anotacao_id} não encontrada nesta sessão.")
    return anotacao


def _secao(request: Request, banco: Banco, sessao, bloco, texto="", erro=None):
    """A seção inteira (formulário + lista): depois de salvar, o formulário volta vazio;
    se der erro, volta com o texto digitado e a mensagem."""
    return html(
        request,
        "sessoes/_anotacoes.html",
        status_code=422 if erro else 200,
        sessao=sessao,
        anotacoes=list(reversed(anotacoes_da_sessao(banco, sessao.id))),
        bloco_anotacao=bloco,
        texto_anotacao=texto,
        erro_anotacao=erro,
    )


@router.post("/sessoes/{sessao_id}/anotacoes")
def criar(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    texto: Annotated[str, Form()] = "",
    bloco: Annotated[str, Form()] = "",
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    try:
        numero = inteiro_ou_nada("Bloco", bloco)
        if numero is not None:
            questionario.bloco(numero)  # o bloco precisa existir
        adicionar_anotacao(banco, sessao_id, texto, bloco=numero)
    except (ValueError, TypeError, KeyError) as erro:
        mensagem = "a anotação está vazia" if not texto.strip() else str(erro)
        return _secao(request, banco, sessao, bloco, texto, mensagem)
    return _secao(request, banco, sessao, bloco)


@router.get("/sessoes/{sessao_id}/anotacoes/{anotacao_id}")
def mostrar(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, anotacao_id: int
):
    sessao, _ = exigir_sessao(banco, catalogo, sessao_id)
    anotacao = _exigir_anotacao(banco, sessao_id, anotacao_id)
    return html(request, "sessoes/_anotacao.html", sessao=sessao, anotacao=anotacao)


@router.get("/sessoes/{sessao_id}/anotacoes/{anotacao_id}/editar")
def editar(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, anotacao_id: int):
    sessao, _ = exigir_sessao(banco, catalogo, sessao_id)
    anotacao = _exigir_anotacao(banco, sessao_id, anotacao_id)
    return html(request, "sessoes/_anotacao.html", sessao=sessao, anotacao=anotacao, editando=True)


@router.post("/sessoes/{sessao_id}/anotacoes/{anotacao_id}")
def salvar(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    anotacao_id: int,
    texto: Annotated[str, Form()] = "",
):
    sessao, _ = exigir_sessao(banco, catalogo, sessao_id)
    anotacao = _exigir_anotacao(banco, sessao_id, anotacao_id)
    try:
        anotacao = editar_anotacao(banco, anotacao_id, texto)
    except (ValueError, TypeError):
        return html(
            request,
            "sessoes/_anotacao.html",
            status_code=422,
            sessao=sessao,
            anotacao=anotacao,
            editando=True,
            texto=texto,
            erro="a anotação está vazia",
        )
    return html(request, "sessoes/_anotacao.html", sessao=sessao, anotacao=anotacao)


@router.post("/sessoes/{sessao_id}/anotacoes/{anotacao_id}/excluir")
def excluir(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, anotacao_id: int
):
    exigir_sessao(banco, catalogo, sessao_id)
    _exigir_anotacao(banco, sessao_id, anotacao_id)
    excluir_anotacao(banco, anotacao_id)
    return HTMLResponse("")  # o item some da lista (hx-swap="outerHTML" com nada)

"""Telas de cliente. Ficam fora da reunião, por isso usam formulários comuns, sem HTMX:
envia, o servidor grava e redireciona (padrão "POST → redirecionamento → GET")."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request

from descoberta.repositorio import (
    Cliente,
    atualizar_cliente,
    criar_cliente,
    criar_sessao,
    excluir_cliente,
    listar_clientes,
    listar_sessoes,
    obter_cliente,
)

from ..dependencias import Banco, CatalogoDep, html, redirecionar
from ..formularios import FormularioCliente, data_iso

router = APIRouter()


def _exigir_cliente(banco: Banco, cliente_id: int) -> Cliente:
    cliente = obter_cliente(banco, cliente_id)
    if cliente is None:
        raise HTTPException(404, f"Cliente {cliente_id} não encontrado.")
    return cliente


def _formulario(request: Request, acao: str, valores: dict, erro: str | None = None):
    return html(
        request,
        "clientes/formulario.html",
        status_code=422 if erro else 200,
        acao=acao,
        valores=valores,
        erro=erro,
    )


def _pagina_do_cliente(request: Request, banco: Banco, cliente: Cliente, erro=None):
    return html(
        request,
        "clientes/detalhe.html",
        status_code=422 if erro else 200,
        cliente=cliente,
        sessoes=listar_sessoes(banco, cliente.id),
        hoje=date.today(),
        erro=erro,
    )


@router.get("/")
def lista(request: Request, banco: Banco):
    return html(request, "clientes/lista.html", clientes=listar_clientes(banco))


@router.get("/clientes/novo")
def novo(request: Request):
    return _formulario(request, "/clientes", {})


@router.post("/clientes")
def cadastrar(request: Request, banco: Banco, dados: Annotated[FormularioCliente, Form()]):
    try:
        cliente = criar_cliente(banco, **dados.campos())
    except (ValueError, TypeError) as erro:
        return _formulario(request, "/clientes", dados.model_dump(), str(erro))
    return redirecionar(request, f"/clientes/{cliente.id}")


@router.get("/clientes/{cliente_id}")
def detalhe(request: Request, banco: Banco, cliente_id: int):
    return _pagina_do_cliente(request, banco, _exigir_cliente(banco, cliente_id))


@router.get("/clientes/{cliente_id}/editar")
def editar(request: Request, banco: Banco, cliente_id: int):
    cliente = _exigir_cliente(banco, cliente_id)
    valores = cliente.model_dump(exclude_none=True)
    return _formulario(request, f"/clientes/{cliente_id}", valores)


@router.post("/clientes/{cliente_id}")
def salvar(
    request: Request, banco: Banco, cliente_id: int, dados: Annotated[FormularioCliente, Form()]
):
    _exigir_cliente(banco, cliente_id)
    try:
        atualizar_cliente(banco, cliente_id, **dados.campos())
    except (ValueError, TypeError) as erro:
        return _formulario(request, f"/clientes/{cliente_id}", dados.model_dump(), str(erro))
    return redirecionar(request, f"/clientes/{cliente_id}")


@router.post("/clientes/{cliente_id}/excluir")
def excluir(request: Request, banco: Banco, cliente_id: int):
    _exigir_cliente(banco, cliente_id)
    excluir_cliente(banco, cliente_id)
    return redirecionar(request, "/")


@router.post("/clientes/{cliente_id}/sessoes")
def abrir_sessao(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    cliente_id: int,
    data: Annotated[str, Form()] = "",
):
    cliente = _exigir_cliente(banco, cliente_id)
    try:
        sessao = criar_sessao(
            banco,
            cliente_id=cliente_id,
            data=data_iso("Data da sessão", data),
            versao_questionario=catalogo.versao_mais_recente,
        )
    except (ValueError, TypeError) as erro:
        return _pagina_do_cliente(request, banco, cliente, str(erro))
    return redirecionar(request, f"/sessoes/{sessao.id}")

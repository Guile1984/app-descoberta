"""Revisão pós-sessão: página própria, separada da tela ao vivo.

Textos do relatório salvam sozinhos (como as respostas). As quatro listas (riscos,
indicadores, escopo e próximos passos) usam as mesmas rotas, com o nome da lista na URL:

    POST /sessoes/1/revisao/riscos              inclui um risco
    GET  /sessoes/1/revisao/riscos/7/editar     o risco 7 em modo de edição
    POST /sessoes/1/revisao/riscos/7            salva a edição
    POST /sessoes/1/revisao/riscos/7/excluir    exclui

Incluir, salvar e excluir devolvem a lista inteira: a numeração dos riscos (R1, R2…) muda
quando um sai, e a lista toda precisa acompanhar a matriz. Toda mudança dispara o evento
"revisao-mudou", que faz a matriz e o quadro de pendências se recarregarem sozinhos.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import SQLModel

from descoberta.questionario import Questionario
from descoberta.repositorio import (
    Sessao,
    adicionar_item,
    editar_item,
    excluir_item,
    itens_da_sessao,
    obter_cliente,
    salvar_texto_secao,
)

from ..dependencias import Banco, CatalogoDep, aviso, exigir_sessao, html
from ..revisao import LISTAS, ROTULOS, ListaRevisao, contexto_da_revisao

router = APIRouter()

EVENTO = "revisao-mudou"


async def _formulario(request: Request) -> dict[str, str]:
    """Os campos do formulário, quaisquer que sejam (cada lista tem os seus)."""
    formulario = await request.form()
    return {campo: valor for campo, valor in formulario.items() if isinstance(valor, str)}


Formulario = Annotated[dict[str, str], Depends(_formulario)]


def _lista(nome: str) -> ListaRevisao:
    if nome not in LISTAS:
        raise HTTPException(404, f"A revisão não tem a lista '{nome}'.")
    return LISTAS[nome]


def _exigir_item(banco: Banco, lista: ListaRevisao, sessao_id: int, item_id: int) -> SQLModel:
    item = banco.get(lista.modelo, item_id)
    if item is None or item.sessao_id != sessao_id:
        raise HTTPException(404, f"Item {item_id} não encontrado nesta sessão.")
    return item


def _avisar(resposta: HTMLResponse) -> HTMLResponse:
    resposta.headers["HX-Trigger"] = EVENTO
    return resposta


def _secao(
    request: Request,
    banco: Banco,
    sessao: Sessao,
    questionario: Questionario,
    lista: ListaRevisao,
    valores: dict[str, str] | None = None,
    erro: str | None = None,
    focar: bool = False,
) -> HTMLResponse:
    """A lista inteira, com o formulário de inclusão (vazio, ou com o que foi digitado e o
    erro). `focar`: depois de incluir, o cursor volta ao primeiro campo (autofocus)."""
    return html(
        request,
        "revisao/_lista.html",
        status_code=422 if erro else 200,
        sessao=sessao,
        questionario=questionario,
        lista=lista,
        itens=itens_da_sessao(banco, lista.modelo, sessao.id),
        valores=valores or {},
        erro=erro,
        focar=focar,
        **ROTULOS,
    )


def _item(request, banco, sessao, questionario, lista, item, **extra) -> HTMLResponse:
    numero = [i.id for i in itens_da_sessao(banco, lista.modelo, sessao.id)].index(item.id) + 1
    return html(
        request,
        "revisao/_item.html",
        status_code=422 if extra.get("erro") else 200,
        sessao=sessao,
        questionario=questionario,
        lista=lista,
        item=item,
        numero=numero,
        **ROTULOS,
        **extra,
    )


# --- Página e partes que se recarregam sozinhas ---


@router.get("/sessoes/{sessao_id}/revisao")
def pagina(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    return html(
        request,
        "revisao/pagina.html",
        cliente=obter_cliente(banco, sessao.cliente_id),
        **contexto_da_revisao(banco, sessao, questionario),
    )


@router.get("/sessoes/{sessao_id}/revisao/pendencias")
def pendencias(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    contexto = contexto_da_revisao(banco, sessao, questionario)
    return html(request, "revisao/_pendencias_conteudo.html", **contexto)


@router.get("/sessoes/{sessao_id}/revisao/matriz")
def matriz(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    contexto = contexto_da_revisao(banco, sessao, questionario)
    return html(request, "revisao/_matriz_conteudo.html", **contexto)


# --- Textos do relatório (salvamento automático) ---


@router.post("/sessoes/{sessao_id}/textos/{secao_id}")
def salvar_texto(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    secao_id: str,
    texto: Annotated[str, Form()] = "",
):
    _, questionario = exigir_sessao(banco, catalogo, sessao_id)
    try:
        questionario.texto_revisao(secao_id)
    except KeyError:
        raise HTTPException(404, f"O questionário não tem o texto '{secao_id}'.") from None
    salvar_texto_secao(banco, sessao_id, secao_id, texto)  # texto vazio apaga
    return aviso(request, evento=EVENTO)


# --- Listas ---


@router.post("/sessoes/{sessao_id}/revisao/{nome}")
def incluir(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    formulario: Formulario,
    sessao_id: int,
    nome: str,
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    lista = _lista(nome)
    try:
        adicionar_item(banco, lista.modelo, sessao_id, **lista.converter(questionario, formulario))
    except (ValueError, TypeError) as erro:
        return _secao(request, banco, sessao, questionario, lista, formulario, str(erro))
    return _avisar(_secao(request, banco, sessao, questionario, lista, focar=True))


@router.get("/sessoes/{sessao_id}/revisao/{nome}/{item_id}")
def mostrar(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, nome: str, item_id: int
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    lista = _lista(nome)
    item = _exigir_item(banco, lista, sessao_id, item_id)
    return _item(request, banco, sessao, questionario, lista, item)


@router.get("/sessoes/{sessao_id}/revisao/{nome}/{item_id}/editar")
def editar(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, nome: str, item_id: int
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    lista = _lista(nome)
    item = _exigir_item(banco, lista, sessao_id, item_id)
    return _item(
        request,
        banco,
        sessao,
        questionario,
        lista,
        item,
        editando=True,
        valores=lista.valores(item),
    )


@router.post("/sessoes/{sessao_id}/revisao/{nome}/{item_id}")
def salvar(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    formulario: Formulario,
    sessao_id: int,
    nome: str,
    item_id: int,
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    lista = _lista(nome)
    item = _exigir_item(banco, lista, sessao_id, item_id)
    try:
        editar_item(banco, lista.modelo, item_id, **lista.converter(questionario, formulario))
    except (ValueError, TypeError) as erro:
        resposta = _item(
            request,
            banco,
            sessao,
            questionario,
            lista,
            item,
            editando=True,
            valores=formulario,
            erro=str(erro),
        )
        # O formulário de edição mira a lista inteira (hx-target). Com erro, a resposta é
        # só o item em edição: HX-Retarget e HX-Reswap mudam o destino da troca.
        resposta.headers["HX-Retarget"] = f"#{lista.nome}-{item_id}"
        resposta.headers["HX-Reswap"] = "outerHTML"
        return resposta
    return _avisar(_secao(request, banco, sessao, questionario, lista))


@router.post("/sessoes/{sessao_id}/revisao/{nome}/{item_id}/excluir")
def excluir(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, nome: str, item_id: int
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    lista = _lista(nome)
    _exigir_item(banco, lista, sessao_id, item_id)
    excluir_item(banco, lista.modelo, item_id)
    return _avisar(_secao(request, banco, sessao, questionario, lista))

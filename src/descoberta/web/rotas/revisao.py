"""Revisão pós-sessão: página própria, separada da tela ao vivo.

Textos do relatório salvam sozinhos (como as respostas). As quatro listas (riscos,
indicadores, escopo e próximos passos) usam as rotas genéricas de `web/listas.py`, com o
nome da lista na URL (/sessoes/1/revisao/riscos…). Toda mudança dispara o evento
"revisao-mudou", que faz a matriz e o quadro de pendências se recarregarem sozinhos.
"""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request

from descoberta.repositorio import (
    CAMPOS_NUMERICOS,
    marcar_hipotese,
    obter_cliente,
    salvar_texto_secao,
)

from ..dependencias import Banco, CatalogoDep, aviso, exigir_sessao, html
from ..listas import registrar_rotas_de_listas
from ..revisao import LISTAS, contexto_da_revisao, contexto_das_listas

router = APIRouter()

EVENTO = "revisao-mudou"


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


# --- Hipóteses dos cálculos ---


@router.post("/sessoes/{sessao_id}/hipoteses/{campo}")
def salvar_hipotese(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    campo: str,
    valor: Annotated[str | None, Form()] = None,
):
    exigir_sessao(banco, catalogo, sessao_id)
    if campo not in CAMPOS_NUMERICOS:
        raise HTTPException(404, f"'{campo}' não é uma métrica numérica.")
    # Caixa de marcar: o navegador só envia o campo quando ela está marcada.
    marcar_hipotese(banco, sessao_id, campo, valor is not None)
    return aviso(request)


# --- Listas (por último: "/revisao/{nome}" combinaria com outras rotas da página) ---

registrar_rotas_de_listas(router, "revisao", LISTAS, EVENTO, contexto_das_listas)

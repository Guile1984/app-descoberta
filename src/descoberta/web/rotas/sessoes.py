"""Página da sessão (abas por bloco e encerramento), partes que se atualizam sozinhas e
salvamento automático dos campos da sessão."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException, Query, Request

from descoberta.questionario import Questionario
from descoberta.repositorio import (
    StatusSessao,
    atualizar_sessao,
    excluir_sessao,
    obter_cliente,
)

from ..atalhos import ATALHOS, atalhos_para_js
from ..contexto import contexto_da_aba, contexto_da_sessao
from ..dependencias import (
    Banco,
    CatalogoDep,
    aviso,
    eh_pedido_htmx,
    exigir_sessao,
    html,
    redirecionar,
)
from .cronometro import contexto_do_cronometro

router = APIRouter()

ENCERRAMENTO = "encerramento"

ROTULOS_STATUS = {
    StatusSessao.preparacao: "Preparação",
    StatusSessao.em_andamento: "Em andamento",
    StatusSessao.concluida: "Concluída",
}


def _aba(questionario: Questionario, valor: str) -> int | str:
    """ "3" → bloco 3; "encerramento" → encerramento; o resto não existe."""
    if valor == ENCERRAMENTO:
        return valor
    if valor.isdigit() and 1 <= int(valor) <= len(questionario.blocos):
        return int(valor)
    raise HTTPException(404, f"O questionário não tem a aba '{valor}'.")


def _pagina_ou_painel(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id, aba):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    aba = _aba(questionario, str(aba))
    contexto = contexto_da_aba(contexto_da_sessao(banco, sessao, questionario), aba)
    # Clique numa aba (HTMX): só o painel, mais os pedaços da coluna direita que dependem
    # da aba (hx-swap-oob). F5 ou link direto: a página inteira.
    if eh_pedido_htmx(request):
        return html(request, "sessoes/_troca_de_aba.html", **contexto)
    return html(
        request,
        "sessoes/pagina.html",
        cliente=obter_cliente(banco, sessao.cliente_id),
        rotulos_status=ROTULOS_STATUS,
        atalhos=ATALHOS,
        atalhos_js=atalhos_para_js(),
        **contexto_do_cronometro(banco, sessao.id, questionario),
        **contexto,
    )


@router.get("/sessoes/{sessao_id}")
def pagina(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    bloco: Annotated[int, Query(ge=1)] = 1,
):
    return _pagina_ou_painel(request, banco, catalogo, sessao_id, bloco)


@router.get("/sessoes/{sessao_id}/encerramento")
def encerramento(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    return _pagina_ou_painel(request, banco, catalogo, sessao_id, ENCERRAMENTO)


# --- Partes da página que se recarregam sozinhas quando um evento chega ---
# Devolvem só o conteúdo: a moldura (com o hx-trigger) fica na página.


def _parte(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id, template, aba="1"):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    contexto = contexto_da_sessao(banco, sessao, questionario)
    return html(request, template, **contexto_da_aba(contexto, _aba(questionario, aba)))


@router.get("/sessoes/{sessao_id}/abas")
def abas(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, atual: str = "1"):
    return _parte(request, banco, catalogo, sessao_id, "sessoes/_abas_conteudo.html", atual)


@router.get("/sessoes/{sessao_id}/pendencias")
def pendencias(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    return _parte(request, banco, catalogo, sessao_id, "sessoes/_pendencias_conteudo.html")


@router.get("/sessoes/{sessao_id}/calculos")
def calculos(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    return _parte(request, banco, catalogo, sessao_id, "sessoes/_calculos_conteudo.html")


@router.get("/sessoes/{sessao_id}/encerramento/resumo")
def resumo(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    return _parte(
        request, banco, catalogo, sessao_id, "sessoes/_resumo_leitura_conteudo.html", ENCERRAMENTO
    )


@router.post("/sessoes/{sessao_id}/excluir")
def excluir(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    sessao, _ = exigir_sessao(banco, catalogo, sessao_id)
    cliente_id = sessao.cliente_id
    excluir_sessao(banco, sessao_id)
    return redirecionar(request, f"/clientes/{cliente_id}")


# --- Salvamento automático dos campos da sessão ---
# Cada campo vem do formulário como texto (ou nada, numa caixa desmarcada) e é convertido
# para o valor que o repositório espera. Campo fora desta lista não pode ser alterado pela
# tela (ex.: a versão do questionário).


def _tipo_solucao(questionario: Questionario, valor: str | None) -> str | None:
    if not valor:
        return None  # bloco 3 ainda em aberto
    if valor not in {tipo.id for tipo in questionario.tipos_solucao}:
        raise ValueError(f"tipo de solução '{valor}' não existe no questionário")
    return valor


_CAMPOS: dict[str, Callable[[Questionario, str | None], Any]] = {
    "status": lambda _q, valor: valor or "",
    "contexto_previo": lambda _q, valor: valor or "",
    # Caixa de marcar: o navegador só envia o campo quando ela está marcada.
    "amostra_dados_recebida": lambda _q, valor: valor is not None,
    "tipo_solucao": _tipo_solucao,
}

# O tipo de solução mostra ou esconde condicionais: muda as obrigatórias pendentes.
_EVENTOS = {"tipo_solucao": "pendencias-mudaram"}


@router.post("/sessoes/{sessao_id}/campos/{campo}")
def salvar_campo(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    campo: str,
    valor: Annotated[str | None, Form()] = None,
):
    _, questionario = exigir_sessao(banco, catalogo, sessao_id)
    if campo not in _CAMPOS:
        raise HTTPException(404, f"Campo '{campo}' não pode ser alterado por aqui.")
    try:
        atualizar_sessao(banco, sessao_id, **{campo: _CAMPOS[campo](questionario, valor)})
    except (ValueError, TypeError) as erro:
        return aviso(request, str(erro))
    return aviso(request, evento=_EVENTOS.get(campo))

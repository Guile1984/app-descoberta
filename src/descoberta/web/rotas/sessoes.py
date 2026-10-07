"""Página da sessão (abas por bloco) e salvamento automático dos campos da sessão."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException, Query, Request

from descoberta.questionario import Questionario, perguntas_visiveis
from descoberta.repositorio import (
    Sessao,
    StatusSessao,
    atualizar_sessao,
    excluir_sessao,
    obter_cliente,
    respostas_da_sessao,
)

from ..dependencias import (
    Banco,
    CatalogoDep,
    aviso,
    eh_pedido_htmx,
    exigir_sessao,
    html,
    redirecionar,
)

router = APIRouter()

ROTULOS_STATUS = {
    StatusSessao.preparacao: "Preparação",
    StatusSessao.em_andamento: "Em andamento",
    StatusSessao.concluida: "Concluída",
}


def _contexto_do_bloco(
    banco: Banco, sessao: Sessao, questionario: Questionario, numero: int
) -> dict[str, Any]:
    perguntas = perguntas_visiveis(questionario, numero, sessao.tipo_solucao)
    return {
        "sessao": sessao,
        "questionario": questionario,
        "bloco": questionario.bloco(numero),
        "obrigatorias": [p for p in perguntas if p.tipo == "obrigatoria"],
        "aprofundamento": [p for p in perguntas if p.tipo == "aprofundamento"],
        "respostas": respostas_da_sessao(banco, sessao.id),
    }


@router.get("/sessoes/{sessao_id}")
def pagina(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    bloco: Annotated[int, Query(ge=1)] = 1,
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    if bloco > len(questionario.blocos):
        raise HTTPException(404, f"O questionário não tem o bloco {bloco}.")
    contexto = _contexto_do_bloco(banco, sessao, questionario, bloco)
    # Clique numa aba (HTMX): só o painel do bloco. F5 ou link direto: a página inteira.
    if eh_pedido_htmx(request):
        return html(request, "sessoes/_bloco.html", **contexto)
    return html(
        request,
        "sessoes/pagina.html",
        cliente=obter_cliente(banco, sessao.cliente_id),
        rotulos_status=ROTULOS_STATUS,
        **contexto,
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
    return aviso(request)

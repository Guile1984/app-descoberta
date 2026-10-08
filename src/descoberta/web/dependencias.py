"""Peças que as rotas recebem prontas do FastAPI (banco, catálogo) e respostas comuns."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from descoberta.questionario import Questionario
from descoberta.repositorio import Sessao, obter_sessao

from .catalogo import Catalogo
from .numeros import moeda, numero, numero_campo

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _id_html(id_questionario: str) -> str:
    # "b4.vc1" → "b4-vc1". Num seletor CSS ("#aviso-b4.vc1"), o ponto quer dizer "classe";
    # o hífen não existe nos ids do YAML, então dois ids nunca viram o mesmo id do HTML.
    return id_questionario.replace(".", "-")


def _data_br(dia: date) -> str:
    return dia.strftime("%d/%m/%Y")


def _hora_local(horario: datetime) -> str:
    # Horários são gravados em UTC (o SQLite devolve sem fuso); a tela mostra a hora local.
    if horario.tzinfo is None:
        horario = horario.replace(tzinfo=UTC)
    return horario.astimezone().strftime("%H:%M")


templates.env.filters["id_html"] = _id_html
templates.env.filters["data_br"] = _data_br
templates.env.filters["hora_local"] = _hora_local
templates.env.filters["moeda"] = moeda
templates.env.filters["numero"] = numero
templates.env.filters["numero_campo"] = numero_campo


def abrir_banco(request: Request) -> Iterator[Session]:
    """Uma Session do banco por pedido, fechada quando a resposta sai."""
    with Session(request.app.state.engine) as session:
        yield session


def obter_catalogo(request: Request) -> Catalogo:
    return request.app.state.catalogo


Banco = Annotated[Session, Depends(abrir_banco)]
CatalogoDep = Annotated[Catalogo, Depends(obter_catalogo)]


def eh_pedido_htmx(request: Request) -> bool:
    """Pedido feito pelo HTMX, que espera só um pedaço da página.

    Quando o usuário usa o botão "voltar", o HTMX pede a página inteira e avisa com o
    cabeçalho HX-History-Restore-Request; nesse caso devolvemos a página completa.
    """
    return (
        request.headers.get("HX-Request") == "true"
        and request.headers.get("HX-History-Restore-Request") != "true"
    )


def html(request: Request, template: str, status_code: int = 200, **contexto: Any) -> HTMLResponse:
    return templates.TemplateResponse(request, template, contexto, status_code=status_code)


def redirecionar(request: Request, url: str) -> Response:
    """Vai para outra página.

    Num pedido do HTMX, um redirecionamento comum (303) seria seguido "por baixo" e a
    página nova seria encaixada dentro da atual. O cabeçalho HX-Redirect pede ao HTMX que
    troque a página inteira.
    """
    if eh_pedido_htmx(request):
        return Response(headers={"HX-Redirect": url})
    return RedirectResponse(url, status_code=303)


def aviso(request: Request, erro: str | None = None, evento: str | None = None) -> HTMLResponse:
    """O pedacinho de HTML que aparece ao lado do campo: "Salvo às…" ou "Não salvo: …".

    `evento`: quando o valor foi salvo, o cabeçalho HX-Trigger faz o HTMX disparar esse
    evento na página. As partes da tela que dependem do valor (cálculos, pendências)
    escutam o evento (hx-trigger="calculos-mudaram from:body") e se recarregam sozinhas.
    """
    resposta = html(
        request,
        "_aviso.html",
        status_code=422 if erro else 200,
        erro=erro,
        hora=datetime.now().strftime("%H:%M:%S"),
    )
    if evento and not erro:
        resposta.headers["HX-Trigger"] = evento
    return resposta


def exigir_sessao(
    banco: Session, catalogo: Catalogo, sessao_id: int
) -> tuple[Sessao, Questionario]:
    """A sessão e o questionário da versão com que ela foi aberta."""
    sessao = obter_sessao(banco, sessao_id)
    if sessao is None:
        raise HTTPException(404, f"Sessão {sessao_id} não encontrada.")
    return sessao, catalogo.questionario(sessao.versao_questionario)

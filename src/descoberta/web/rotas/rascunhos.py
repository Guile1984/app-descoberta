"""Rascunhos por LLM: painel, pessoas citadas, prévia, gerar, aceitar e descartar.

- GET  /sessoes/1/llm/painel?pagina=revisao     o painel (recarrega no evento llm-mudou)
- POST /sessoes/1/llm/pessoas                   inclui uma pessoa citada
- POST /sessoes/1/llm/pessoas/7/remover         tira da lista
- GET  /sessoes/1/llm/previa?pagina=revisao     o que sairia para o LLM (anotacoes=1: com as
                                                anotações internas)
- POST /sessoes/1/llm/previa                    confirma a prévia vista (impressao)
- POST /sessoes/1/revisao/textos/<id>/rascunho  gera o rascunho de um texto da revisão
- POST /sessoes/1/rascunhos/9/aceitar           copia o rascunho para o texto
- POST /sessoes/1/rascunhos/9/descartar         só marca como descartado

Erros voltam com o código 422, que o HTMX desta app troca na tela (veja base.html).
"""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from sqlmodel import Session

from descoberta.llm.contexto import pedido_da_revisao
from descoberta.llm.provedor import LLMIndisponivel
from descoberta.llm.rascunho import previa_do_pedido
from descoberta.repositorio import (
    DestinoRascunho,
    PessoaCitada,
    Rascunho,
    SituacaoRascunho,
    aceitar_rascunho_da_revisao,
    adicionar_pessoa_citada,
    confirmar_previa,
    descartar_rascunho,
    rascunho_pendente,
    remover_pessoa_citada,
)

from ..dependencias import Banco, CatalogoDep, exigir_sessao, html
from ..llm import (
    EVENTO_LLM,
    PAGINAS,
    TEXTO_CONTINUA,
    Alvo,
    alvo_da_revisao,
    gerar_e_registrar,
    pedido_da_previa,
    sessao_para_llm,
    situacao_do_provedor,
)
from ..revisao import contexto_da_revisao

router = APIRouter()

Texto = Annotated[str, Form()]


def _pagina(pagina: str) -> str:
    if pagina not in PAGINAS:
        raise HTTPException(404, f"Página desconhecida: '{pagina}'.")
    return pagina


def painel(request, banco, catalogo, sessao_id, pagina, erro=None):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    return html(
        request,
        "llm/_painel_conteudo.html",
        status_code=422 if erro else 200,
        sessao=sessao,
        pagina=pagina,
        llm=sessao_para_llm(banco, sessao, questionario, catalogo),
        provedor=situacao_do_provedor(request),
        erro=erro,
    )


@router.get("/sessoes/{sessao_id}/llm/painel")
def ver_painel(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, pagina: str = "revisao"
):
    return painel(request, banco, catalogo, sessao_id, _pagina(pagina))


@router.post("/sessoes/{sessao_id}/llm/pessoas")
def incluir_pessoa(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    nome: Texto = "",
    pagina: Texto = "revisao",
):
    exigir_sessao(banco, catalogo, sessao_id)
    try:
        adicionar_pessoa_citada(banco, sessao_id, nome)
    except (ValueError, TypeError) as erro:
        banco.rollback()
        return painel(request, banco, catalogo, sessao_id, _pagina(pagina), str(erro))
    return painel(request, banco, catalogo, sessao_id, _pagina(pagina))


@router.post("/sessoes/{sessao_id}/llm/pessoas/{pessoa_id}/remover")
def remover_pessoa(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    pessoa_id: int,
    pagina: Texto = "revisao",
):
    exigir_sessao(banco, catalogo, sessao_id)
    pessoa = banco.get(PessoaCitada, pessoa_id)
    if pessoa is None or pessoa.sessao_id != sessao_id:
        raise HTTPException(404, "Pessoa não encontrada nesta sessão.")
    remover_pessoa_citada(banco, pessoa_id)
    return painel(request, banco, catalogo, sessao_id, _pagina(pagina))


@router.get("/sessoes/{sessao_id}/llm/previa")
def ver_previa(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    pagina: str = "revisao",
    anotacoes: str = "",
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    llm = sessao_para_llm(banco, sessao, questionario, catalogo)
    com_anotacoes = bool(anotacoes)
    pedido = pedido_da_previa(request.app.state.prompts, llm, _pagina(pagina), com_anotacoes)
    return html(
        request,
        "llm/_previa.html",
        sessao=sessao,
        pagina=pagina,
        previa=previa_do_pedido(pedido, llm.anonimizador()),
        impressao=llm.impressao,
        anotacoes=com_anotacoes,
    )


@router.post("/sessoes/{sessao_id}/llm/previa")
def confirmar(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    impressao: Texto = "",
    pagina: Texto = "revisao",
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    atual = sessao_para_llm(banco, sessao, questionario, catalogo).impressao
    if impressao != atual:
        erro = "Os dados mudaram desde esta prévia: veja a prévia de novo antes de confirmar."
        return painel(request, banco, catalogo, sessao_id, _pagina(pagina), erro)
    confirmar_previa(banco, sessao_id, impressao)
    resposta = painel(request, banco, catalogo, sessao_id, _pagina(pagina))
    resposta.headers["HX-Trigger"] = EVENTO_LLM
    return resposta


# --- Rascunho de um campo ---


def bloco_do_rascunho(
    request, sessao_id: int, alvo: Alvo, rascunho: Rascunho | None, erro: str | None = None
):
    return html(
        request,
        "llm/_rascunho.html",
        status_code=422 if erro else 200,
        sessao_id=sessao_id,
        alvo=alvo,
        rascunho=rascunho,
        erro=erro,
    )


@router.post("/sessoes/{sessao_id}/revisao/textos/{texto_id}/rascunho")
def gerar_texto_da_revisao(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    texto_id: str,
    anotacoes: Texto = "",
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    try:
        questionario.texto_revisao(texto_id)
    except KeyError:
        raise HTTPException(404, f"O questionário não tem o texto '{texto_id}'.") from None
    alvo = alvo_da_revisao(sessao_id, texto_id)
    llm = sessao_para_llm(banco, sessao, questionario, catalogo)
    com_anotacoes = bool(anotacoes)
    try:
        rascunho = gerar_e_registrar(
            request,
            banco,
            sessao,
            llm,
            prompt_id="rascunho_revisao",
            montar_pedido=lambda prompt: pedido_da_revisao(
                prompt, llm.dados, texto_id, anotacoes_internas=com_anotacoes
            ),
            destino=DestinoRascunho.revisao,
            campo=texto_id,
            anotacoes=com_anotacoes,
            chave_limite=texto_id,
        )
    except LLMIndisponivel as erro:
        pendente = rascunho_pendente(banco, sessao_id, DestinoRascunho.revisao, texto_id)
        return bloco_do_rascunho(
            request, sessao_id, alvo, pendente, f"{erro.motivo} {TEXTO_CONTINUA}"
        )
    return bloco_do_rascunho(request, sessao_id, alvo, rascunho)


def _rascunho_da_sessao(banco: Session, sessao_id: int, rascunho_id: int) -> Rascunho:
    rascunho = banco.get(Rascunho, rascunho_id)
    if rascunho is None or rascunho.sessao_id != sessao_id:
        raise HTTPException(404, "Rascunho não encontrado nesta sessão.")
    return rascunho


def _alvo(sessao_id: int, rascunho: Rascunho) -> Alvo:
    if rascunho.destino is DestinoRascunho.revisao:
        return alvo_da_revisao(sessao_id, rascunho.campo)
    from ..proposta import alvo_da_proposta

    return alvo_da_proposta(sessao_id, rascunho.campo)


def _texto_da_revisao(request, banco, sessao, questionario, texto_id, erro=None):
    contexto = contexto_da_revisao(banco, sessao, questionario)
    return html(
        request,
        "revisao/_texto.html",
        status_code=422 if erro else 200,
        t=questionario.texto_revisao(texto_id),
        erro_rascunho=erro,
        **contexto,
    )


@router.post("/sessoes/{sessao_id}/rascunhos/{rascunho_id}/aceitar")
def aceitar(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, rascunho_id: int
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    rascunho = _rascunho_da_sessao(banco, sessao_id, rascunho_id)
    if rascunho.destino is DestinoRascunho.proposta:
        from .proposta import aceitar_rascunho_na_proposta

        return aceitar_rascunho_na_proposta(request, banco, catalogo, sessao, rascunho)
    try:
        aceitar_rascunho_da_revisao(banco, rascunho_id)
    except ValueError as erro:
        banco.rollback()
        return _texto_da_revisao(request, banco, sessao, questionario, rascunho.campo, str(erro))
    resposta = _texto_da_revisao(request, banco, sessao, questionario, rascunho.campo)
    resposta.headers["HX-Trigger"] = "revisao-mudou"
    return resposta


@router.post("/sessoes/{sessao_id}/rascunhos/{rascunho_id}/descartar")
def descartar(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, rascunho_id: int
):
    exigir_sessao(banco, catalogo, sessao_id)
    rascunho = _rascunho_da_sessao(banco, sessao_id, rascunho_id)
    alvo = _alvo(sessao_id, rascunho)
    if rascunho.situacao is not SituacaoRascunho.pendente:
        erro = f"Este rascunho já foi {rascunho.situacao}."
        return bloco_do_rascunho(request, sessao_id, alvo, None, erro)
    descartar_rascunho(banco, rascunho_id)
    return bloco_do_rascunho(request, sessao_id, alvo, None)

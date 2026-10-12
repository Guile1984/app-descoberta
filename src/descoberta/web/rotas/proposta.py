"""Proposta Comercial: criação, edição (salvamento automático e listas) e documento.

- GET /sessoes/1/proposta: sem proposta, a página de criação; com proposta, a edição.
- POST /sessoes/1/proposta: cria a proposta como cópia do modelo (YAML) e da revisão. Se
  o score final estiver numa faixa de alerta ("não seguir agora"), a app avisa e só cria
  com a confirmação (campo "confirmar").
- POST /sessoes/1/proposta/campo/<campo>: salva um campo (salvamento automático).
- POST /sessoes/1/proposta/recriar: apaga a proposta (não as versões registradas) para
  criar de novo a partir da revisão.
- GET /sessoes/1/proposta/documento e /sessoes/1/proposta.<formato>: prévia e downloads.
- As listas (fases, escopo…) usam as rotas genéricas de `web/listas.py`.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from sqlmodel import Session

from descoberta.formatos import slug
from descoberta.proposta import ModeloProposta
from descoberta.proposta.inicial import conteudo_inicial
from descoberta.questionario import Questionario
from descoberta.relatorio import (
    DadosProposta,
    DadosRelatorio,
    EmissaoProposta,
    coletar_dados,
    coletar_dados_proposta,
    dados_para_proposta_nova,
    emitir_proposta,
)
from descoberta.relatorio.dados_proposta import faixa_do_score_final
from descoberta.relatorio.documento import FALTA
from descoberta.repositorio import (
    Sessao,
    criar_proposta,
    excluir_proposta,
    obter_cliente,
    obter_proposta,
    salvar_proposta,
)
from descoberta.repositorio.modelos import agora

from ..dependencias import Banco, CatalogoDep, aviso, exigir_sessao, html, redirecionar
from ..listas import registrar_rotas_de_listas
from ..proposta import (
    CAMPOS_DAS_CONDICOES,
    CAMPOS_DO_CLIENTE,
    EVENTO,
    LISTAS,
    contexto_das_listas,
    converter_campo,
)
from .relatorio import FORMATOS, arquivo

router = APIRouter()


def _modelo(catalogo: CatalogoDep, versao: int | None = None) -> ModeloProposta:
    try:
        return catalogo.modelo_proposta(versao or catalogo.versao_modelo_proposta)
    except LookupError as erro:
        raise HTTPException(404, f"Não foi possível abrir o modelo da proposta: {erro}") from None


def _dados_relatorio(banco: Session, sessao: Sessao, questionario: Questionario):
    try:
        return coletar_dados(banco, sessao.id, questionario)
    except ValueError as erro:  # dado gravado que o questionário da sessão não reconhece
        raise HTTPException(422, f"Não foi possível ler a sessão: {erro}") from None


def _alerta(dados: DadosRelatorio, modelo: ModeloProposta) -> str | None:
    """ "nao_seguir": o score final está numa faixa de alerta; "incompleto": sem score."""
    faixa = faixa_do_score_final(dados)
    if faixa is None:
        return "incompleto"
    return "nao_seguir" if faixa in modelo.alerta_score_final else None


def _dados_proposta(banco: Banco, catalogo: CatalogoDep, sessao_id: int) -> DadosProposta:
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    proposta = obter_proposta(banco, sessao_id)
    if proposta is None:
        raise HTTPException(404, "A sessão ainda não tem proposta. Crie a proposta primeiro.")
    modelo = _modelo(catalogo, proposta.versao_modelo)
    _dados_relatorio(banco, sessao, questionario)  # 422 legível se a sessão não fecha
    return coletar_dados_proposta(banco, sessao_id, questionario, modelo)


def _nome_do_arquivo(empresa: str, data: date, extensao: str, numero: int | None = None) -> str:
    """proposta-comercial-construtora-alvorada-2026-10-07-v1.pdf (só ASCII)."""
    sufixo = f"-v{numero}" if numero else ""
    return f"proposta-comercial-{slug(empresa)}-{data.isoformat()}{sufixo}.{extensao}"


def _pagina_de_criacao(request, banco, sessao, questionario, catalogo, status_code=200):
    modelo = _modelo(catalogo)
    dados = _dados_relatorio(banco, sessao, questionario)
    return html(
        request,
        "proposta/criar.html",
        status_code=status_code,
        sessao=sessao,
        cliente=obter_cliente(banco, sessao.cliente_id),
        modelo=modelo,
        alerta=_alerta(dados, modelo),
        score_final=dados.painel.score_final,
        inicial=conteudo_inicial(modelo.padrao, dados_para_proposta_nova(dados)),
    )


@router.get("/sessoes/{sessao_id}/proposta")
def pagina(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    proposta = obter_proposta(banco, sessao_id)
    if proposta is None:
        return _pagina_de_criacao(request, banco, sessao, questionario, catalogo)
    modelo = _modelo(catalogo, proposta.versao_modelo)
    dados = _dados_relatorio(banco, sessao, questionario)
    return html(
        request,
        "proposta/pagina.html",
        sessao=sessao,
        cliente=obter_cliente(banco, sessao.cliente_id),
        proposta=proposta,
        modelo=modelo,
        alerta=_alerta(dados, modelo),
        score_final=dados.painel.score_final,
        listas=LISTAS,
        itens={nome: lista.itens(banco, sessao_id) for nome, lista in LISTAS.items()},
        campos_do_cliente=CAMPOS_DO_CLIENTE,
        campos_das_condicoes=CAMPOS_DAS_CONDICOES,
        **contexto_das_listas(banco, sessao, questionario),
    )


@router.post("/sessoes/{sessao_id}/proposta")
def criar(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    confirmar: Annotated[str, Form()] = "",
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    if obter_proposta(banco, sessao_id) is not None:
        raise HTTPException(409, "A sessão já tem proposta. Para começar de novo, use Recriar.")
    modelo = _modelo(catalogo)
    dados = _dados_relatorio(banco, sessao, questionario)
    alerta = _alerta(dados, modelo)
    if alerta == "nao_seguir" and not confirmar:
        # 409: o pedido conflita com a recomendação; a página explica e pede confirmação.
        return _pagina_de_criacao(request, banco, sessao, questionario, catalogo, 409)
    criar_proposta(
        banco,
        sessao_id,
        conteudo_inicial(modelo.padrao, dados_para_proposta_nova(dados)),
        versao_modelo=modelo.versao,
        com_alerta=alerta == "nao_seguir",
    )
    return redirecionar(request, f"/sessoes/{sessao_id}/proposta")


@router.post("/sessoes/{sessao_id}/proposta/recriar")
def recriar(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    exigir_sessao(banco, catalogo, sessao_id)
    excluir_proposta(banco, sessao_id)
    return redirecionar(request, f"/sessoes/{sessao_id}/proposta")


@router.post("/sessoes/{sessao_id}/proposta/campo/{campo}")
def salvar_campo(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    campo: str,
    valor: Annotated[str, Form()] = "",
):
    exigir_sessao(banco, catalogo, sessao_id)
    campos = {c for c, _, _ in CAMPOS_DO_CLIENTE + CAMPOS_DAS_CONDICOES}
    if campo not in campos:
        raise HTTPException(404, f"A proposta não tem o campo '{campo}'.")
    if obter_proposta(banco, sessao_id) is None:
        raise HTTPException(404, "A sessão ainda não tem proposta.")
    try:
        salvar_proposta(banco, sessao_id, **{campo: converter_campo(campo, valor)})
    except (ValueError, TypeError) as erro:
        banco.rollback()
        return aviso(request, str(erro))
    return aviso(request, evento=EVENTO)


@router.get("/sessoes/{sessao_id}/proposta/documento")
def documento(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    dados = _dados_proposta(banco, catalogo, sessao_id)
    emitida = emitir_proposta(dados, EmissaoProposta(numero=None, emitido_em=agora()))
    sessao, _ = exigir_sessao(banco, catalogo, sessao_id)
    return html(
        request,
        "proposta/documento.html",
        sessao=sessao,
        dados=dados,
        modelo=dados.modelo,
        documento=emitida.documento,
        a_preencher=emitida.markdown.count(FALTA),
    )


@router.get("/sessoes/{sessao_id}/proposta.{formato}")
def baixar(banco: Banco, catalogo: CatalogoDep, sessao_id: int, formato: str):
    if formato not in FORMATOS:
        raise HTTPException(404, f"A proposta não é exportada em '{formato}'.")
    dados = _dados_proposta(banco, catalogo, sessao_id)
    emitida = emitir_proposta(dados, EmissaoProposta(numero=None, emitido_em=agora()))
    tipo_conteudo, exportar = FORMATOS[formato]
    nome = _nome_do_arquivo(dados.relatorio.empresa, dados.relatorio.data_sessao, formato)
    return arquivo(exportar(emitida), tipo_conteudo, nome)


# --- Listas (por último: "/proposta/{nome}" combinaria com as rotas acima) ---

registrar_rotas_de_listas(router, "proposta", LISTAS, EVENTO, contexto_das_listas)

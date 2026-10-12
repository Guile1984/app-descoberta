"""Proposta Comercial: criação, edição (salvamento automático e listas) e documento.

- GET /sessoes/1/proposta: sem proposta, a página de criação; com proposta, a edição.
- POST /sessoes/1/proposta: cria a proposta como cópia do modelo (YAML) e da revisão. Se
  o score final estiver numa faixa de alerta ("não seguir agora"), a app avisa e só cria
  com a confirmação (campo "confirmar").
- POST /sessoes/1/proposta/campo/<campo>: salva um campo (salvamento automático).
- POST /sessoes/1/proposta/textos/contexto: salva o "Contexto da proposta".
- POST /sessoes/1/proposta/textos/contexto/rascunho e
  POST /sessoes/1/proposta/fases/<id>/objetivo/rascunho: rascunhos por LLM (as regras e o
  aceitar/descartar ficam em web/rotas/rascunhos.py e web/llm.py).
- GET /sessoes/1/proposta/avisos: item repetido entre fases e total diferente do
  investimento da métrica; recarregado a cada mudança (evento "proposta-mudou").
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
from descoberta.llm.contexto import pedido_da_proposta
from descoberta.llm.provedor import LLMIndisponivel
from descoberta.proposta import MARCADORES, ModeloProposta
from descoberta.proposta.clausulas import Ajuste, conferir_ajuste
from descoberta.proposta.inicial import conteudo_inicial
from descoberta.questionario import Questionario
from descoberta.relatorio import (
    DadosProposta,
    DadosRelatorio,
    Emissao,
    EmissaoProposta,
    coletar_dados,
    coletar_dados_proposta,
    dados_para_proposta_nova,
    emitir,
    emitir_proposta,
    exportar_pdf,
)
from descoberta.relatorio.dados_proposta import faixa_do_score_final
from descoberta.relatorio.documento import FALTA
from descoberta.relatorio.exportar.juntar import Parte, juntar_pdfs
from descoberta.relatorio.proposta import condicoes_gerais
from descoberta.repositorio import (
    CAMPOS_TEXTO_PROPOSTA,
    DestinoRascunho,
    FaseProposta,
    Rascunho,
    RegistroNaoEncontrado,
    Sessao,
    TipoVersao,
    aceitar_rascunho_da_proposta,
    ajustar_clausula,
    ajustes_das_clausulas,
    criar_proposta,
    excluir_proposta,
    obter_cliente,
    obter_proposta,
    obter_versao_proposta,
    proximo_numero_versao_proposta,
    registrar_versao_proposta,
    restaurar_clausula,
    salvar_proposta,
    salvar_texto_proposta,
    textos_da_proposta,
    versoes_da_proposta,
    versoes_da_sessao,
)
from descoberta.repositorio.modelos import agora
from descoberta.rotulos import UFS

from ..dependencias import Banco, CatalogoDep, aviso, exigir_sessao, html, redirecionar
from ..listas import registrar_rotas_de_listas
from ..llm import TEXTO_CONTINUA, gerar_e_registrar, sessao_para_llm, situacao_do_provedor
from ..proposta import (
    CAMPOS_DAS_CONDICOES,
    CAMPOS_DO_CLIENTE,
    EVENTO,
    LISTAS,
    alvo_da_proposta,
    avisos,
    avisos_da_proposta_gravada,
    clausula_na_tela,
    clausulas_na_tela,
    contexto_das_listas,
    converter_campo,
    rascunhos_pendentes_da_proposta,
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
    inicial = conteudo_inicial(modelo.padrao, dados_para_proposta_nova(dados))
    fases = [(f.nome, f.escopo, f.investimento) for f in inicial.fases]
    return html(
        request,
        "proposta/criar.html",
        status_code=status_code,
        sessao=sessao,
        cliente=obter_cliente(banco, sessao.cliente_id),
        modelo=modelo,
        alerta=_alerta(dados, modelo),
        score_final=dados.painel.score_final,
        inicial=inicial,
        avisos=avisos(fases, dados.entradas.investimento),
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
        ufs=UFS,
        clausulas=clausulas_na_tela(modelo, ajustes_das_clausulas(banco, sessao_id)),
        marcadores=MARCADORES,
        avisos=avisos_da_proposta_gravada(banco, sessao_id, dados.entradas.investimento),
        pagina="proposta",
        llm=sessao_para_llm(banco, sessao, questionario, catalogo),
        provedor=situacao_do_provedor(request),
        **_contexto_do_texto(banco, sessao_id),
        **contexto_das_listas(banco, sessao, questionario),
    )


def _contexto_do_texto(banco: Session, sessao_id: int) -> dict:
    """O que proposta/_contexto.html usa: o texto, o rascunho pendente e o alvo."""
    return {
        "textos_proposta": textos_da_proposta(banco, sessao_id),
        "rascunho_contexto": rascunhos_pendentes_da_proposta(banco, sessao_id).get("contexto"),
        "alvo_contexto": alvo_da_proposta(sessao_id, "contexto"),
    }


# --- Textos narrativos e rascunhos por LLM ---


@router.post("/sessoes/{sessao_id}/proposta/textos/{campo}")
def salvar_texto(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    campo: str,
    texto: Annotated[str, Form()] = "",
):
    exigir_sessao(banco, catalogo, sessao_id)
    if campo not in CAMPOS_TEXTO_PROPOSTA:
        raise HTTPException(404, f"A proposta não tem o texto '{campo}'.")
    if obter_proposta(banco, sessao_id) is None:
        raise HTTPException(404, "A sessão ainda não tem proposta.")
    salvar_texto_proposta(banco, sessao_id, campo, texto)
    return aviso(request, evento=EVENTO)


def _gerar_na_proposta(request, banco, catalogo, sessao_id, campo, anotacoes, montar):
    """Gera um rascunho de texto da proposta; `montar(prompt, proposta)` faz o pedido."""
    from .rascunhos import bloco_do_rascunho

    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    llm = sessao_para_llm(banco, sessao, questionario, catalogo)
    if llm.proposta is None:
        raise HTTPException(404, "A sessão ainda não tem proposta.")
    alvo = alvo_da_proposta(sessao_id, campo)
    com_anotacoes = bool(anotacoes)
    try:
        rascunho = gerar_e_registrar(
            request,
            banco,
            sessao,
            llm,
            prompt_id="rascunho_proposta",
            montar_pedido=lambda prompt: montar(prompt, llm.proposta, com_anotacoes),
            destino=DestinoRascunho.proposta,
            campo=campo,
            anotacoes=com_anotacoes,
        )
    except LLMIndisponivel as erro:
        pendente = rascunhos_pendentes_da_proposta(banco, sessao_id).get(campo)
        return bloco_do_rascunho(
            request, sessao_id, alvo, pendente, f"{erro.motivo} {TEXTO_CONTINUA}"
        )
    return bloco_do_rascunho(request, sessao_id, alvo, rascunho)


@router.post("/sessoes/{sessao_id}/proposta/textos/contexto/rascunho")
def gerar_contexto(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    anotacoes: Annotated[str, Form()] = "",
):
    def montar(prompt, proposta, com_anotacoes):
        return pedido_da_proposta(
            prompt,
            proposta,
            "contexto",
            texto_atual=proposta.contexto or "",
            anotacoes_internas=com_anotacoes,
        )

    return _gerar_na_proposta(request, banco, catalogo, sessao_id, "contexto", anotacoes, montar)


@router.post("/sessoes/{sessao_id}/proposta/fases/{fase_id}/objetivo/rascunho")
def gerar_objetivo_da_fase(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    fase_id: int,
    anotacoes: Annotated[str, Form()] = "",
):
    exigir_sessao(banco, catalogo, sessao_id)
    fase = banco.get(FaseProposta, fase_id)
    if fase is None or fase.sessao_id != sessao_id:
        raise HTTPException(404, "Fase não encontrada nesta proposta.")

    def montar(prompt, proposta, com_anotacoes):
        posicao = next(i for i, f in enumerate(proposta.fases) if f.id == fase_id)
        return pedido_da_proposta(
            prompt,
            proposta,
            "objetivo_fase",
            fase=posicao,
            texto_atual=fase.objetivo or "",
            anotacoes_internas=com_anotacoes,
        )

    campo = f"objetivo_fase.{fase_id}"
    return _gerar_na_proposta(request, banco, catalogo, sessao_id, campo, anotacoes, montar)


def aceitar_rascunho_na_proposta(
    request: Request, banco: Session, catalogo, sessao: Sessao, rascunho: Rascunho
):
    """Aceitar um rascunho da proposta: devolve o campo inteiro com o texto novo."""
    _, questionario = exigir_sessao(banco, catalogo, sessao.id)
    erro = None
    try:
        aceitar_rascunho_da_proposta(banco, rascunho.id)
    except (ValueError, RegistroNaoEncontrado) as falha:
        banco.rollback()
        erro = str(falha)
    if rascunho.campo == "contexto":
        resposta = html(
            request,
            "proposta/_contexto.html",
            status_code=422 if erro else 200,
            sessao=sessao,
            erro_rascunho=erro,
            **_contexto_do_texto(banco, sessao.id),
        )
        if not erro:
            resposta.headers["HX-Trigger"] = EVENTO
        return resposta
    fase_id = int(rascunho.campo.removeprefix("objetivo_fase."))
    lista = LISTAS["fases"]
    itens = lista.itens(banco, sessao.id)
    fase = next((f for f in itens if f.id == fase_id), None)
    if fase is None:
        raise HTTPException(404, "Fase não encontrada nesta proposta.")
    resposta = html(
        request,
        "listas/_item.html",
        status_code=422 if erro else 200,
        sessao=sessao,
        lista=lista,
        item=fase,
        numero=[f.id for f in itens].index(fase_id) + 1,
        editando=False,
        erro_rascunho=erro,
        **contexto_das_listas(banco, sessao, questionario),
    )
    if not erro:
        resposta.headers["HX-Trigger"] = f"{EVENTO}, fases-mudaram"
    return resposta


@router.get("/sessoes/{sessao_id}/proposta/avisos")
def avisos_da_proposta(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    """Os avisos de novo, depois de uma mudança na proposta (evento proposta-mudou)."""
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    if obter_proposta(banco, sessao_id) is None:
        raise HTTPException(404, "A sessão ainda não tem proposta.")
    investimento = _dados_relatorio(banco, sessao, questionario).entradas.investimento
    return html(
        request,
        "proposta/_avisos_conteudo.html",
        sessao=sessao,
        avisos=avisos_da_proposta_gravada(banco, sessao_id, investimento),
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
        versoes=versoes_da_proposta(banco, sessao_id),
        pacote=_versoes_do_pacote(banco, sessao_id),
    )


@router.post("/sessoes/{sessao_id}/proposta/versoes")
def registrar(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    """Gera o PDF com o próximo número e guarda (PDF, hashes e Condições Gerais)."""
    dados = _dados_proposta(banco, catalogo, sessao_id)
    numero = proximo_numero_versao_proposta(banco, sessao_id)
    emitida = emitir_proposta(dados, EmissaoProposta(numero=numero, emitido_em=agora()))
    registrar_versao_proposta(
        banco,
        sessao_id,
        numero=numero,
        emitido_em=emitida.emissao.emitido_em,
        conteudo_md=emitida.markdown,
        pdf=exportar_pdf(emitida),
        versao_modelo=dados.modelo.versao,
        clausulas=condicoes_gerais(dados),
    )
    # POST → redirecionamento → GET: o F5 na página seguinte não registra de novo.
    return redirecionar(request, f"/sessoes/{sessao_id}/proposta/documento#versoes")


@router.get("/sessoes/{sessao_id}/proposta/versoes/{numero}.pdf")
def baixar_versao(banco: Banco, catalogo: CatalogoDep, sessao_id: int, numero: int):
    sessao, _ = exigir_sessao(banco, catalogo, sessao_id)
    versao = obter_versao_proposta(banco, sessao_id, numero)
    if versao is None:
        raise HTTPException(404, f"A proposta não tem a versão {numero} registrada.")
    empresa = obter_cliente(banco, sessao.cliente_id).empresa
    nome = _nome_do_arquivo(empresa, sessao.data, "pdf", numero)
    return arquivo(versao.pdf, "application/pdf", nome)


def _versoes_do_pacote(banco: Banco, sessao_id: int):
    """As partes do PDF único: a última versão registrada do relatório para o cliente (a
    interna nunca vai) e a última da proposta; None onde ainda não há versão."""
    relatorio = next(
        (v for v in versoes_da_sessao(banco, sessao_id) if v.tipo == TipoVersao.cliente), None
    )
    proposta = next(iter(versoes_da_proposta(banco, sessao_id)), None)
    return relatorio, proposta


@router.get("/sessoes/{sessao_id}/proposta/relatorio-e-proposta.pdf")
def baixar_juntos(banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    """Relatório e proposta num PDF só; sem versão registrada, entra o rascunho."""
    dados = _dados_proposta(banco, catalogo, sessao_id)
    relatorio, proposta = _versoes_do_pacote(banco, sessao_id)
    momento = agora()
    if relatorio is None:
        emissao = Emissao(TipoVersao.cliente, numero=None, emitido_em=momento)
        pdf_relatorio = exportar_pdf(emitir(dados.relatorio, emissao))
    else:
        pdf_relatorio = relatorio.pdf
    if proposta is None:
        pdf_proposta = exportar_pdf(emitir_proposta(dados, EmissaoProposta(None, momento)))
    else:
        pdf_proposta = proposta.pdf
    empresa, data = dados.relatorio.empresa, dados.relatorio.data_sessao
    junto = juntar_pdfs(
        f"Relatório de Descoberta e {dados.modelo.titulo} — {empresa}",
        [Parte("Relatório de Descoberta", pdf_relatorio), Parte(dados.modelo.titulo, pdf_proposta)],
    )
    nome = f"relatorio-e-proposta-{slug(empresa)}-{data.isoformat()}.pdf"
    return arquivo(junto, "application/pdf", nome)


@router.get("/sessoes/{sessao_id}/proposta.{formato}")
def baixar(banco: Banco, catalogo: CatalogoDep, sessao_id: int, formato: str):
    if formato not in FORMATOS:
        raise HTTPException(404, f"A proposta não é exportada em '{formato}'.")
    dados = _dados_proposta(banco, catalogo, sessao_id)
    emitida = emitir_proposta(dados, EmissaoProposta(numero=None, emitido_em=agora()))
    tipo_conteudo, exportar = FORMATOS[formato]
    nome = _nome_do_arquivo(dados.relatorio.empresa, dados.relatorio.data_sessao, formato)
    return arquivo(exportar(emitida), tipo_conteudo, nome)


# --- Condições Gerais (ajustes das cláusulas nesta proposta) ---


def _modelo_da_proposta(banco: Banco, catalogo: CatalogoDep, sessao_id: int) -> ModeloProposta:
    exigir_sessao(banco, catalogo, sessao_id)
    proposta = obter_proposta(banco, sessao_id)
    if proposta is None:
        raise HTTPException(404, "A sessão ainda não tem proposta.")
    return _modelo(catalogo, proposta.versao_modelo)


def _exigir_clausula(modelo: ModeloProposta, clausula_id: str) -> None:
    try:
        modelo.clausula(clausula_id)
    except KeyError:
        raise HTTPException(404, f"O modelo não tem a cláusula '{clausula_id}'.") from None


def _clausula(request, banco, sessao_id, modelo, clausula_id, erro=None):
    ajuste = ajustes_das_clausulas(banco, sessao_id).get(clausula_id, Ajuste())
    return html(
        request,
        "proposta/_clausula.html",
        status_code=422 if erro else 200,
        sessao_id=sessao_id,
        clausula=clausula_na_tela(modelo, clausula_id, ajuste),
        erro=erro,
    )


@router.post("/sessoes/{sessao_id}/proposta/clausulas/{clausula_id}")
def ajustar_texto(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    clausula_id: str,
    texto: Annotated[str, Form()] = "",
):
    """Salvamento automático do texto da cláusula nesta proposta."""
    modelo = _modelo_da_proposta(banco, catalogo, sessao_id)
    _exigir_clausula(modelo, clausula_id)
    if not texto.strip():
        return aviso(request, "o texto não pode ficar vazio; para tirar a cláusula, use Excluir")
    try:
        conferir_ajuste(modelo, clausula_id, texto=texto)
    except ValueError as erro:
        return aviso(request, str(erro))
    if texto.strip() == modelo.clausula(clausula_id).texto.strip():
        restaurar_clausula(banco, sessao_id, clausula_id)  # igual ao modelo: sem ajuste
    else:
        ajustar_clausula(banco, sessao_id, clausula_id, texto=texto)
    return aviso(request, evento=EVENTO)


@router.post("/sessoes/{sessao_id}/proposta/clausulas/{clausula_id}/restaurar")
def restaurar(
    request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, clausula_id: str
):
    modelo = _modelo_da_proposta(banco, catalogo, sessao_id)
    _exigir_clausula(modelo, clausula_id)
    restaurar_clausula(banco, sessao_id, clausula_id)
    resposta = _clausula(request, banco, sessao_id, modelo, clausula_id)
    resposta.headers["HX-Trigger"] = EVENTO
    return resposta


@router.post("/sessoes/{sessao_id}/proposta/clausulas/{clausula_id}/excluir")
def excluir_ou_incluir(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    clausula_id: str,
    excluir: Annotated[str, Form()] = "1",
):
    """excluir=1 tira a cláusula desta proposta; excluir=0 inclui de volta."""
    modelo = _modelo_da_proposta(banco, catalogo, sessao_id)
    _exigir_clausula(modelo, clausula_id)
    excluida = excluir == "1"
    try:
        conferir_ajuste(modelo, clausula_id, excluida=excluida)
    except ValueError as erro:
        return _clausula(request, banco, sessao_id, modelo, clausula_id, str(erro))
    ajustar_clausula(banco, sessao_id, clausula_id, excluida=excluida)
    resposta = _clausula(request, banco, sessao_id, modelo, clausula_id)
    resposta.headers["HX-Trigger"] = EVENTO
    return resposta


# --- Listas (por último: "/proposta/{nome}" combinaria com as rotas acima) ---

registrar_rotas_de_listas(router, "proposta", LISTAS, EVENTO, contexto_das_listas)

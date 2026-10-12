"""O LLM na tela: qual provedor usar, a situação do painel e a geração de um rascunho.

Regras que valem para todas as telas (revisão e proposta):
- nunca durante a sessão ao vivo (cronômetro rodando);
- só depois de o consultor ver e confirmar a prévia do que sai (vale enquanto a impressão
  dos dados conhecidos não muda);
- falha do LLM vira aviso: o texto atual e o relatório por template continuam.
"""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import HTTPException, Request
from sqlmodel import Session

from descoberta.llm.anonimizacao import (
    Anonimizador,
    Conhecido,
    impressao_dos_conhecidos,
    sugerir_nomes,
)
from descoberta.llm.contexto import (
    conhecidos_da_sessao,
    pedido_da_proposta,
    pedido_da_revisao,
    textos_para_sugestao,
)
from descoberta.llm.prompts import Pedido, Prompt
from descoberta.llm.provedor import LLMIndisponivel, ProvedorLLM, criar_provedor
from descoberta.llm.rascunho import gerar_rascunho
from descoberta.questionario import Questionario
from descoberta.relatorio import DadosProposta, DadosRelatorio, coletar_dados
from descoberta.relatorio.dados_proposta import coletar_dados_proposta
from descoberta.repositorio import (
    DestinoRascunho,
    PessoaCitada,
    Rascunho,
    Sessao,
    obter_proposta,
    pessoas_citadas,
    previa_confirmada,
    registrar_rascunho,
    tempo_do_cronometro,
)

from .catalogo import Catalogo

EVENTO_LLM = "llm-mudou"
PAGINAS = ("revisao", "proposta")

SESSAO_AO_VIVO = (
    "O cronômetro da sessão está rodando: o LLM não é usado durante a sessão ao vivo. "
    "Pause o cronômetro na tela da sessão para gerar rascunhos."
)
PREVIA_PENDENTE = (
    "Antes do primeiro rascunho, veja a prévia do que sai para o LLM e confirme "
    "(no painel ao lado)."
)
TEXTO_CONTINUA = "O texto atual continua como está, e o relatório por template continua disponível."


def obter_provedor(request: Request) -> ProvedorLLM:
    """O provedor injetado (testes) ou o da configuração; LLMIndisponivel se não houver."""
    injetado = getattr(request.app.state, "provedor_llm", None)
    if injetado is not None:
        return injetado
    return criar_provedor(request.app.state.config_llm)


@dataclass(frozen=True)
class SituacaoDoProvedor:
    ativo: bool
    descricao: str  # "claude · claude-opus-5-5" ou o motivo de estar indisponível


def situacao_do_provedor(request: Request) -> SituacaoDoProvedor:
    try:
        provedor = obter_provedor(request)
    except LLMIndisponivel as erro:
        return SituacaoDoProvedor(False, erro.motivo)
    return SituacaoDoProvedor(True, f"{provedor.nome} · {provedor.modelo}")


@dataclass(frozen=True)
class SessaoParaLLM:
    """O que o painel e a geração precisam saber da sessão."""

    dados: DadosRelatorio
    proposta: DadosProposta | None
    pessoas: list[PessoaCitada]
    conhecidos: list[Conhecido]
    impressao: str
    previa_ok: bool
    ao_vivo: bool
    sugestoes: list[str]

    def anonimizador(self) -> Anonimizador:
        return Anonimizador(self.conhecidos)


def sessao_para_llm(
    banco: Session,
    sessao: Sessao,
    questionario: Questionario,
    catalogo: Catalogo,
    dados: DadosRelatorio | None = None,
) -> SessaoParaLLM:
    """`dados`: a sessão já lida pela página, para não ler tudo de novo."""
    if dados is None:
        try:
            dados = coletar_dados(banco, sessao.id, questionario)
        except ValueError as erro:  # dado gravado que o questionário não reconhece
            raise HTTPException(422, f"Não foi possível ler a sessão: {erro}") from None
    proposta = None
    registro = obter_proposta(banco, sessao.id)
    if registro is not None:
        try:
            modelo = catalogo.modelo_proposta(registro.versao_modelo)
        except LookupError:
            modelo = None
        if modelo is not None:
            proposta = coletar_dados_proposta(
                banco, sessao.id, questionario, modelo, relatorio=dados
            )
    pessoas = pessoas_citadas(banco, sessao.id)
    conhecidos = conhecidos_da_sessao(dados, proposta, [p.nome for p in pessoas])
    impressao = impressao_dos_conhecidos(conhecidos)
    ja_conhecidos = [c.valor for c in conhecidos if c.tipo != "literal"]
    return SessaoParaLLM(
        dados=dados,
        proposta=proposta,
        pessoas=pessoas,
        conhecidos=conhecidos,
        impressao=impressao,
        previa_ok=previa_confirmada(banco, sessao.id, impressao),
        ao_vivo=tempo_do_cronometro(banco, sessao.id)[1],
        sugestoes=sugerir_nomes(textos_para_sugestao(dados), ignorar=ja_conhecidos),
    )


def pedido_da_previa(
    prompts: dict[str, Prompt], llm: SessaoParaLLM, pagina: str, anotacoes: bool
) -> Pedido:
    """Um pedido representativo da página, para a prévia (os dados trocados são os mesmos
    em todos os textos da sessão)."""
    if pagina == "proposta" and llm.proposta is not None:
        return pedido_da_proposta(
            prompts["rascunho_proposta"], llm.proposta, "contexto", anotacoes_internas=anotacoes
        )
    primeiro = llm.dados.questionario.revisao.textos[0].id
    return pedido_da_revisao(
        prompts["rascunho_revisao"], llm.dados, primeiro, anotacoes_internas=anotacoes
    )


@dataclass(frozen=True)
class Alvo:
    """Onde o rascunho de um campo aparece na tela e para onde vão os botões."""

    id_html: str  # o bloco do rascunho (gerar e descartar trocam só ele)
    url_gerar: str
    aceitar: str  # seletor do que "aceitar" troca (o campo inteiro, com o texto novo)


def alvo_da_revisao(sessao_id: int, texto_id: str) -> Alvo:
    return Alvo(
        id_html=f"rascunho-{texto_id}",
        url_gerar=f"/sessoes/{sessao_id}/revisao/textos/{texto_id}/rascunho",
        aceitar=f"#bloco-texto-{texto_id}",
    )


def gerar_e_registrar(
    request: Request,
    banco: Session,
    sessao: Sessao,
    llm: SessaoParaLLM,
    *,
    prompt_id: str,
    montar_pedido: Callable[[Prompt], Pedido],
    destino: DestinoRascunho,
    campo: str,
    anotacoes: bool,
    chave_limite: str,
) -> Rascunho:
    """Confere as regras, gera e guarda o rascunho pendente (LLMIndisponivel se não der)."""
    if llm.ao_vivo:
        raise LLMIndisponivel(SESSAO_AO_VIVO)
    provedor = obter_provedor(request)
    if not llm.previa_ok:
        raise LLMIndisponivel(PREVIA_PENDENTE)
    prompt = request.app.state.prompts[prompt_id]
    gerado = gerar_rascunho(
        provedor,
        prompt.rotulo,
        montar_pedido(prompt),
        llm.anonimizador(),
        limite_palavras=prompt.limites_palavras.get(chave_limite),
    )
    return registrar_rascunho(
        banco,
        sessao.id,
        destino=destino,
        campo=campo,
        texto=gerado.texto,
        provedor=gerado.provedor,
        modelo=gerado.modelo,
        versao_prompt=gerado.versao_prompt,
        alertas=gerado.alertas,
        com_anotacoes_internas=anotacoes,
    )

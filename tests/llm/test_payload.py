"""Critério de aceite do Sprint 7: nenhum dado pessoal no payload enviado ao LLM.

O caso Roberto inteiro (respostas, anotações, revisão, proposta, perfil do consultor) é
enviado, texto por texto, por um provedor Claude com o SDK de verdade e um transporte
falso. O teste lê o corpo exato de cada pedido HTTP e procura cada dado pessoal do demo,
sem ligar para maiúsculas e acentos.
"""

import json
import unicodedata

import anthropic
import httpx2
import pytest
from pydantic import SecretStr

from descoberta.llm.anonimizacao import Anonimizador, sugerir_nomes
from descoberta.llm.claude import ProvedorClaude
from descoberta.llm.configuracao import ConfigClaude
from descoberta.llm.contexto import (
    conhecidos_da_sessao,
    contexto_da_sessao,
    pedido_da_proposta,
    pedido_da_revisao,
    textos_para_sugestao,
)
from descoberta.llm.rascunho import gerar_rascunho

PESSOAS_CITADAS = ["Marcos", "Cida"]

# Todos os dados pessoais do caso Roberto, como estão no demo.
DADOS_PESSOAIS = [
    "Roberto",
    "Construtora Alvorada",
    "Alvorada",
    "Marcos",
    "Cida",
    "Ana Exemplo",
    "Exemplo Consultoria",
    "roberto@example.com",
    "ana@example.com",
    "11.222.333/0001-81",
    "11222333000181",
    "12.ABC.345/01DE-35",
    "12ABC34501DE35",
    "(11) 90000-0000",
    "90000-0000",
    "Campinas",
    "São Paulo",
]


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()


class _APICapturando:
    def __init__(self):
        self.corpos: list[str] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.corpos.append(request.content.decode("utf-8"))
        corpo = json.loads(request.content)
        assert "[CLIENTE]" in corpo["messages"][0]["content"]  # a anonimização rodou
        return httpx2.Response(
            200,
            json={
                "id": "msg",
                "type": "message",
                "role": "assistant",
                "model": "claude-opus-5-5",
                "content": [{"type": "text", "text": "O [CLIENTE] e o [PESSOA_1], da [EMPRESA]."}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )


@pytest.fixture
def api():
    return _APICapturando()


@pytest.fixture
def provedor(api):
    cliente_http = anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(api))
    return ProvedorClaude(
        ConfigClaude(tentativas=0), SecretStr("sk-" + "ant-teste"), http_client=cliente_http
    )


def _pedidos(prompts, dados, proposta):
    for texto in dados.questionario.revisao.textos:
        yield pedido_da_revisao(prompts["rascunho_revisao"], dados, texto.id)
    yield pedido_da_proposta(prompts["rascunho_proposta"], proposta, "contexto")
    for i, _ in enumerate(proposta.fases):
        yield pedido_da_proposta(prompts["rascunho_proposta"], proposta, "objetivo_fase", fase=i)


def test_nenhum_dado_pessoal_sai_no_payload(
    api, provedor, prompts, dados_roberto, proposta_roberto
):
    conhecidos = conhecidos_da_sessao(dados_roberto, proposta_roberto, PESSOAS_CITADAS)
    rascunhos = []
    for pedido in _pedidos(prompts, dados_roberto, proposta_roberto):
        anonimizador = Anonimizador(conhecidos)
        rascunhos.append(gerar_rascunho(provedor, "rascunho_vX", pedido, anonimizador))

    assert len(api.corpos) == 6 + 1 + len(proposta_roberto.fases)
    for corpo in api.corpos:
        enviado = _normalizar(
            json.loads(corpo)["system"] + json.loads(corpo)["messages"][0]["content"]
        )
        bruto = _normalizar(corpo)
        for dado in DADOS_PESSOAIS:
            assert _normalizar(dado) not in enviado, dado
            assert _normalizar(dado) not in bruto, dado
        # Os números de negócio continuam lá: o LLM precisa deles.
        assert "r$ 20.000,00" in enviado
        assert "7,7 meses" in enviado
    # E voltam na resposta, localmente.
    assert rascunhos[0].texto == "O Roberto e o Marcos, da Construtora Alvorada."
    assert rascunhos[0].alertas == ()


def test_por_padrao_nenhuma_anotacao_nem_sinal_sai(
    api, provedor, prompts, dados_roberto, proposta_roberto
):
    """Os rascunhos são para textos que o cliente lê: como na versão cliente do relatório,
    anotações do consultor e sinais de alerta só saem se ele pedir."""
    conhecidos = conhecidos_da_sessao(dados_roberto, proposta_roberto, PESSOAS_CITADAS)
    for pedido in _pedidos(prompts, dados_roberto, proposta_roberto):
        gerar_rascunho(provedor, "rascunho_vX", pedido, Anonimizador(conhecidos))
    questionario = dados_roberto.questionario
    textos_dos_sinais = {s.id: s.texto for b in questionario.blocos for s in b.sinais}
    internos = [textos_dos_sinais[s.id] for s in dados_roberto.sinais]
    internos += [s.observacao for s in dados_roberto.sinais if s.observacao]
    # As anotações como sairiam (anonimizadas): nem assim podem aparecer.
    anonimizador = Anonimizador(conhecidos)
    internos += [anonimizador.anonimizar(a.texto) for a in dados_roberto.anotacoes]
    assert dados_roberto.anotacoes
    assert dados_roberto.sinais
    for corpo in api.corpos:
        mensagem = json.loads(corpo)["messages"][0]["content"]
        assert "Anotações do consultor" not in mensagem
        assert "Sinais de alerta" not in mensagem
        for texto in internos:
            assert texto not in mensagem, texto


def test_com_a_opcao_as_anotacoes_saem_anonimizadas(api, provedor, prompts, dados_roberto):
    conhecidos = conhecidos_da_sessao(dados_roberto, None, PESSOAS_CITADAS)
    pedido = pedido_da_revisao(
        prompts["rascunho_revisao"], dados_roberto, "recomendacao", anotacoes_internas=True
    )
    gerar_rascunho(provedor, "rascunho_vX", pedido, Anonimizador(conhecidos))
    mensagem = json.loads(api.corpos[-1])["messages"][0]["content"]
    assert "[PESSOA_1] não participou" in mensagem  # anotação, com o nome trocado
    assert "Marcos" not in mensagem


def test_a_sugestao_de_nomes_pega_as_pessoas_citadas_do_demo(dados_roberto):
    """Sem a lista, "Marcos" e "Cida" sairiam: por isso a prévia é obrigatória e a app
    sugere os nomes. No caso Roberto, a sugestão traz exatamente os dois."""
    sugestao = sugerir_nomes(
        textos_para_sugestao(dados_roberto),
        ignorar=[dados_roberto.cliente, dados_roberto.empresa],
    )
    assert sugestao == ["Marcos", "Cida"]


def test_sem_a_lista_de_pessoas_o_nome_citado_escaparia(dados_roberto):
    """Documenta o limite: nome solto, fora da lista e sem formato reconhecível, não é
    detectado sozinho. A prévia obrigatória (tela da revisão) cobre esse caso."""
    a = Anonimizador(conhecidos_da_sessao(dados_roberto, None, []))
    assert "Marcos" in a.anonimizar(contexto_da_sessao(dados_roberto))

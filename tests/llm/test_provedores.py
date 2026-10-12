"""Provedores (API Claude, Ollama local, falso) e a falha segura: sem chamadas reais.

A API Claude é testada com o SDK de verdade e um transporte falso (httpx2.MockTransport):
o pedido é montado pelo SDK como seria enviado, mas nunca sai da máquina. O Ollama é
testado com um servidor HTTP local, de mentira, nesta máquina.
"""

import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import anthropic
import httpx2
import pytest
from pydantic import SecretStr

from descoberta.llm.claude import ProvedorClaude
from descoberta.llm.configuracao import (
    ConfigClaude,
    ConfigOllama,
    ConfiguracaoLLM,
    Provedor,
)
from descoberta.llm.falso import ProvedorFalso
from descoberta.llm.ollama import ProvedorOllama
from descoberta.llm.prompts import Pedido
from descoberta.llm.provedor import LLMIndisponivel, criar_provedor

CHAVE = "sk-ant-api03-SENTINELA-QUE-NUNCA-PODE-APARECER"
PEDIDO = Pedido("Instruções fixas.", "Escreva o rascunho para [CLIENTE].")


def _mensagem(texto="Rascunho para [CLIENTE].", stop_reason="end_turn", modelo="claude-opus-5-5"):
    conteudo = [{"type": "text", "text": texto}] if texto is not None else []
    return {
        "id": "msg_teste",
        "type": "message",
        "role": "assistant",
        "model": modelo,
        "content": conteudo,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }


class _API:
    """A API da Anthropic de mentira: guarda os pedidos e responde o que o teste mandar."""

    def __init__(self, responder):
        self.pedidos: list[httpx2.Request] = []
        self._responder = responder

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.pedidos.append(request)
        return self._responder(request)

    @property
    def corpo(self) -> dict:
        return json.loads(self.pedidos[-1].content)


def _claude(api: _API, **config) -> ProvedorClaude:
    cliente_http = anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(api))
    return ProvedorClaude(
        ConfigClaude(tentativas=0, **config), SecretStr(CHAVE), http_client=cliente_http
    )


def _erro(status: int, tipo: str):
    corpo = {"type": "error", "error": {"type": tipo, "message": f"falhou; chave {CHAVE}"}}
    return lambda request: httpx2.Response(status, json=corpo)


# --- API Claude ---


def test_claude_monta_o_pedido_com_o_modelo_e_o_esforco():
    api = _API(lambda r: httpx2.Response(200, json=_mensagem()))
    resposta = _claude(api).redigir(PEDIDO)
    assert resposta.texto == "Rascunho para [CLIENTE]."
    assert resposta.modelo == "claude-opus-5-5"
    assert resposta.alerta is None
    assert api.corpo == {
        "model": "claude-opus-5-5",
        "max_tokens": 16000,
        "system": "Instruções fixas.",
        "messages": [{"role": "user", "content": "Escreva o rascunho para [CLIENTE]."}],
        "output_config": {"effort": "medium"},
    }
    assert str(api.pedidos[-1].url) == "https://api.anthropic.com/v1/messages"


def test_claude_atende_varios_pedidos_seguidos():
    api = _API(lambda r: httpx2.Response(200, json=_mensagem()))
    provedor = _claude(api)
    for _ in range(3):
        provedor.redigir(PEDIDO)
    assert len(api.pedidos) == 3


def test_claude_sem_reenvio_automatico_em_caso_de_recusa():
    api = _API(lambda r: httpx2.Response(200, json=_mensagem(None, stop_reason="refusal")))
    with pytest.raises(LLMIndisponivel, match="recusou"):
        _claude(api).redigir(PEDIDO)
    assert len(api.pedidos) == 1
    assert "fallbacks" not in api.corpo
    assert "anthropic-beta" not in api.pedidos[-1].headers


def test_claude_guarda_o_modelo_que_respondeu():
    api = _API(lambda r: httpx2.Response(200, json=_mensagem(modelo="claude-opus-5-5-x")))
    assert _claude(api).redigir(PEDIDO).modelo == "claude-opus-5-5-x"


def test_claude_resposta_cortada_vira_alerta():
    api = _API(lambda r: httpx2.Response(200, json=_mensagem("Texto", stop_reason="max_tokens")))
    resposta = _claude(api).redigir(PEDIDO)
    assert resposta.texto == "Texto"
    assert "cortada" in resposta.alerta


def test_claude_resposta_vazia():
    api = _API(lambda r: httpx2.Response(200, json=_mensagem("   ")))
    with pytest.raises(LLMIndisponivel, match="vazia"):
        _claude(api).redigir(PEDIDO)


def _sem_rede(request):
    raise httpx2.ConnectError("sem rede", request=request)


def _lento(request):
    raise httpx2.ReadTimeout("lento", request=request)


@pytest.mark.parametrize(
    ("responder", "motivo"),
    [
        (_sem_rede, "sem conexão com a internet"),
        (_lento, "demorou demais"),
        (_erro(401, "authentication_error"), "chave da API foi recusada"),
        (_erro(403, "permission_error"), "não tem permissão"),
        (_erro(404, "not_found_error"), "config/llm.yaml"),
        (_erro(429, "rate_limit_error"), "limite de uso"),
        (_erro(400, "invalid_request_error"), "não aceitou o pedido"),
        (_erro(500, "api_error"), "fora do ar ou sobrecarregado"),
        (_erro(529, "overloaded_error"), "fora do ar ou sobrecarregado"),
    ],
)
def test_claude_falha_segura(responder, motivo, caplog):
    caplog.set_level(logging.DEBUG)
    with pytest.raises(LLMIndisponivel) as erro:
        _claude(_API(responder)).redigir(PEDIDO)
    assert motivo in erro.value.motivo
    # A mensagem é fixa: nada do erro original (que poderia trazer a chave) passa adiante.
    assert CHAVE not in str(erro.value)
    assert erro.value.__cause__ is None
    assert erro.value.__suppress_context__
    assert CHAVE not in caplog.text


def test_chave_so_no_cabecalho_e_nunca_nos_logs(caplog):
    caplog.set_level(logging.DEBUG)
    api = _API(lambda r: httpx2.Response(200, json=_mensagem()))
    provedor = _claude(api)
    provedor.redigir(PEDIDO)
    assert api.pedidos[-1].headers["x-api-key"] == CHAVE
    assert CHAVE not in api.pedidos[-1].content.decode()
    assert CHAVE not in caplog.text
    assert CHAVE not in repr(provedor)
    assert CHAVE not in str(vars(provedor))


# --- Ollama (modelo local) ---


class _Ollama(BaseHTTPRequestHandler):
    resposta: tuple[int, bytes] = (200, b"{}")
    atraso = 0.0
    recebidos: list[dict] = []

    def do_POST(self):
        tamanho = int(self.headers["Content-Length"])
        _Ollama.recebidos.append({"path": self.path, "corpo": json.loads(self.rfile.read(tamanho))})
        time.sleep(_Ollama.atraso)
        status, corpo = _Ollama.resposta
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


@pytest.fixture
def ollama():
    _Ollama.recebidos = []
    _Ollama.atraso = 0.0
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), _Ollama)
    servidor.daemon_threads = True
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    host, porta = servidor.server_address

    def provedor(status=200, corpo=None, atraso=0.0, tempo_limite_s=5.0):
        if corpo is None:
            corpo = {"model": "llama3.1:8b", "message": {"content": "Olá [CLIENTE]"}, "done": True}
        _Ollama.resposta = (
            status,
            corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode(),
        )
        _Ollama.atraso = atraso
        config = ConfigOllama(url=f"http://{host}:{porta}", tempo_limite_s=tempo_limite_s)
        return ProvedorOllama(config)

    yield provedor
    servidor.shutdown()
    servidor.server_close()


def test_ollama_monta_o_pedido(ollama):
    resposta = ollama().redigir(PEDIDO)
    assert resposta.texto == "Olá [CLIENTE]"
    assert resposta.modelo == "llama3.1:8b"
    [recebido] = _Ollama.recebidos
    assert recebido["path"] == "/api/chat"
    assert recebido["corpo"] == {
        "model": "llama3.1:8b",
        "stream": False,
        "messages": [
            {"role": "system", "content": "Instruções fixas."},
            {"role": "user", "content": "Escreva o rascunho para [CLIENTE]."},
        ],
    }


def test_ollama_ignora_proxy_do_sistema(ollama, monkeypatch):
    # Um proxy configurado no Windows não pode desviar os dados do modelo local.
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:9")
    assert ollama().redigir(PEDIDO).texto == "Olá [CLIENTE]"


def test_ollama_resposta_cortada(ollama):
    corpo = {"model": "m", "message": {"content": "Texto"}, "done": True, "done_reason": "length"}
    assert "cortada" in ollama(corpo=corpo).redigir(PEDIDO).alerta


@pytest.mark.parametrize(
    ("kwargs", "motivo"),
    [
        ({"status": 404, "corpo": {"error": "model not found"}}, "ollama pull llama3.1:8b"),
        ({"status": 500, "corpo": {"error": "x"}}, "O Ollama respondeu com erro (código 500)"),
        ({"corpo": b"isto nao e json"}, "resposta que não deu para ler"),
        ({"corpo": {"model": "m", "message": {"content": "  "}}}, "vazia"),
        ({"atraso": 1.0, "tempo_limite_s": 0.2}, "demorou demais"),
    ],
)
def test_ollama_falha_segura(ollama, kwargs, motivo):
    with pytest.raises(LLMIndisponivel, match=motivo.replace("(", r"\(").replace(")", r"\)")):
        ollama(**kwargs).redigir(PEDIDO)


def test_ollama_parado():
    # Porta sem ninguém ouvindo, nesta máquina.
    provedor = ProvedorOllama(ConfigOllama(url="http://127.0.0.1:9"))
    with pytest.raises(LLMIndisponivel, match="não está rodando"):
        provedor.redigir(PEDIDO)


# --- Escolha do provedor ---


def test_desligado():
    with pytest.raises(LLMIndisponivel, match="desligados"):
        criar_provedor(ConfiguracaoLLM(), ambiente={})


def test_claude_sem_chave():
    config = ConfiguracaoLLM(provedor=Provedor.claude)
    with pytest.raises(LLMIndisponivel, match="ANTHROPIC_API_KEY"):
        criar_provedor(config, ambiente={})


def test_claude_com_chave():
    config = ConfiguracaoLLM(provedor=Provedor.claude)
    provedor = criar_provedor(config, ambiente={"ANTHROPIC_API_KEY": CHAVE})
    assert isinstance(provedor, ProvedorClaude)
    assert provedor.nome == "claude"
    assert provedor.modelo == "claude-opus-5-5"


def test_ollama_escolhido():
    provedor = criar_provedor(ConfiguracaoLLM(provedor=Provedor.ollama), ambiente={})
    assert isinstance(provedor, ProvedorOllama)
    assert (provedor.nome, provedor.modelo) == ("ollama", "llama3.1:8b")


# --- Falso (testes e demonstração) ---


def test_falso_guarda_os_pedidos_e_pode_falhar():
    falso = ProvedorFalso("Texto de teste")
    assert falso.redigir(PEDIDO).texto == "Texto de teste"
    assert falso.pedidos == [PEDIDO]
    with pytest.raises(LLMIndisponivel, match="teste"):
        ProvedorFalso(erro=LLMIndisponivel("falha de teste")).redigir(PEDIDO)

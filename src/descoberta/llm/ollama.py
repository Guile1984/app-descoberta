"""Provedor de modelo local, pelo Ollama (http://localhost:11434), sem pacote extra.

Usa a API /api/chat do Ollama com a biblioteca padrão do Python. O endereço só pode ser
desta máquina (conferido na configuração), e o pedido ignora proxies do sistema: os dados
não passam por nenhum outro computador.
"""

import json
import socket
import urllib.error
import urllib.request

from .configuracao import ConfigOllama
from .prompts import Pedido
from .provedor import RESPOSTA_CORTADA, LLMIndisponivel, Resposta

OLLAMA_PARADO = (
    "O Ollama não está rodando nesta máquina. Abra o Ollama (ou rode 'ollama serve') e "
    "tente de novo."
)
TEMPO_ESGOTADO = "O modelo local demorou demais para responder. Tente de novo."
RESPOSTA_ILEGIVEL = "O Ollama devolveu uma resposta que não deu para ler."
RESPOSTA_VAZIA = "O modelo local devolveu uma resposta vazia."

# Sem ProxyHandler configurado, o urllib usaria o proxy do sistema (HTTP_PROXY).
_ABRIR_SEM_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class ProvedorOllama:
    nome = "ollama"

    def __init__(self, config: ConfigOllama):
        self._config = config

    @property
    def modelo(self) -> str:
        return self._config.modelo

    def redigir(self, pedido: Pedido) -> Resposta:
        corpo = {
            "model": self.modelo,
            "stream": False,
            "messages": [
                {"role": "system", "content": pedido.sistema},
                {"role": "user", "content": pedido.mensagem},
            ],
        }
        # S310: a URL vem de config/llm.yaml, já validada como http:// neste computador
        # (llm.configuracao); file: ou outro esquema não chegam aqui.
        requisicao = urllib.request.Request(  # noqa: S310
            f"{self._config.url}/api/chat",
            data=json.dumps(corpo).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with _ABRIR_SEM_PROXY.open(requisicao, timeout=self._config.tempo_limite_s) as r:
                dados = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            if erro.code == 404:
                raise LLMIndisponivel(
                    f"O modelo {self.modelo!r} não está instalado no Ollama: rode "
                    f"'ollama pull {self.modelo}'."
                ) from None
            raise LLMIndisponivel(f"O Ollama respondeu com erro (código {erro.code}).") from None
        except TimeoutError:
            raise LLMIndisponivel(TEMPO_ESGOTADO) from None
        except urllib.error.URLError as erro:
            if isinstance(erro.reason, TimeoutError | socket.timeout):
                raise LLMIndisponivel(TEMPO_ESGOTADO) from None
            raise LLMIndisponivel(OLLAMA_PARADO) from None
        except (ConnectionError, OSError):
            raise LLMIndisponivel(OLLAMA_PARADO) from None
        except ValueError:  # JSON inválido (inclui UnicodeDecodeError)
            raise LLMIndisponivel(RESPOSTA_ILEGIVEL) from None
        mensagem = dados.get("message") if isinstance(dados, dict) else None
        texto = (mensagem.get("content") or "").strip() if isinstance(mensagem, dict) else ""
        if not texto:
            raise LLMIndisponivel(RESPOSTA_VAZIA)
        alerta = RESPOSTA_CORTADA if dados.get("done_reason") == "length" else None
        return Resposta(texto, str(dados.get("model") or self.modelo), alerta)

"""Provedor da API da Anthropic (Claude), com o SDK oficial.

- Um pedido simples à Messages API: instruções em `system`, o pedido como mensagem do
  usuário e o esforço da configuração. O pensamento do modelo fica no padrão (no Claude
  Opus 5.5 ele é sempre adaptativo e não se desliga).
- Recusa do modelo: vira um aviso, sem reenviar para outro modelo (decisão do sprint).
- Erros viram `LLMIndisponivel` com mensagem fixa, com `from None`: o erro original não
  vai para o log nem para a tela.
- A chave chega como SecretStr e só é aberta na hora de criar o cliente do SDK, que a manda
  no cabeçalho x-api-key.
"""

import anthropic
from pydantic import SecretStr

from .configuracao import ConfigClaude
from .prompts import Pedido
from .provedor import RESPOSTA_CORTADA, LLMIndisponivel, Resposta

SEM_CONEXAO = "Não foi possível falar com a API: sem conexão com a internet."
TEMPO_ESGOTADO = "A API demorou demais para responder. Tente de novo em instantes."
CHAVE_RECUSADA = "A chave da API foi recusada. Confira ANTHROPIC_API_KEY no .env."
SEM_PERMISSAO = "A chave da API não tem permissão para este pedido."
MODELO_NAO_ENCONTRADO = "A API não encontrou o modelo configurado (confira config/llm.yaml)."
LIMITE_DE_USO = "A API atingiu o limite de uso. Espere um pouco e tente de novo."
PEDIDO_RECUSADO = "A API não aceitou o pedido."
FORA_DO_AR = "O serviço da API está fora do ar ou sobrecarregado. Tente de novo mais tarde."
RECUSA = (
    "O modelo recusou este pedido e nenhum rascunho foi gerado. Escreva o texto à mão ou "
    "tente de novo."
)
RESPOSTA_VAZIA = "A API devolveu uma resposta vazia."


class ProvedorClaude:
    nome = "claude"

    def __init__(self, config: ConfigClaude, chave: SecretStr, http_client=None):
        self._config = config
        self._chave = chave
        self._http_client = http_client  # só nos testes (transporte falso)

    @property
    def modelo(self) -> str:
        return self._config.modelo

    def __repr__(self) -> str:
        return f"ProvedorClaude(modelo={self.modelo!r})"

    def redigir(self, pedido: Pedido) -> Resposta:
        cliente = anthropic.Anthropic(
            api_key=self._chave.get_secret_value(),
            timeout=self._config.tempo_limite_s,
            max_retries=self._config.tentativas,
            http_client=self._http_client,
        )
        try:
            mensagem = cliente.messages.create(
                model=self._config.modelo,
                max_tokens=self._config.max_tokens,
                system=pedido.sistema,
                messages=[{"role": "user", "content": pedido.mensagem}],
                output_config={"effort": self._config.esforco},
            )
        except anthropic.APITimeoutError:  # antes de APIConnectionError, que é a mãe
            raise LLMIndisponivel(TEMPO_ESGOTADO) from None
        except anthropic.APIConnectionError:
            raise LLMIndisponivel(SEM_CONEXAO) from None
        except anthropic.AuthenticationError:
            raise LLMIndisponivel(CHAVE_RECUSADA) from None
        except anthropic.PermissionDeniedError:
            raise LLMIndisponivel(SEM_PERMISSAO) from None
        except anthropic.NotFoundError:
            raise LLMIndisponivel(MODELO_NAO_ENCONTRADO) from None
        except anthropic.RateLimitError:
            raise LLMIndisponivel(LIMITE_DE_USO) from None
        except anthropic.APIStatusError as erro:
            if erro.status_code >= 500:
                raise LLMIndisponivel(FORA_DO_AR) from None
            raise LLMIndisponivel(f"{PEDIDO_RECUSADO} (código {erro.status_code})") from None
        finally:
            if self._http_client is None:  # só fecha a conexão que ele mesmo abriu
                cliente.close()
        if mensagem.stop_reason == "refusal":
            raise LLMIndisponivel(RECUSA)
        texto = "".join(b.text for b in mensagem.content if b.type == "text").strip()
        if not texto:
            raise LLMIndisponivel(RESPOSTA_VAZIA)
        alerta = RESPOSTA_CORTADA if mensagem.stop_reason == "max_tokens" else None
        return Resposta(texto, mensagem.model, alerta)

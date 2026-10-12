"""Interface comum dos provedores de LLM e a escolha pela configuração.

Todo provedor recebe um `Pedido` (já anonimizado por quem chama) e devolve uma `Resposta`
ou levanta `LLMIndisponivel` com um motivo em português, para a tela mostrar. O motivo é
sempre um texto fixo: nada do erro original passa adiante (ele poderia trazer detalhes do
pedido ou da chave).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from .configuracao import ConfiguracaoLLM, Provedor, ler_chave_api
from .prompts import Pedido

RESPOSTA_CORTADA = "A resposta foi cortada no limite de tamanho: confira o fim do texto."


class LLMIndisponivel(Exception):
    """Não deu para gerar o rascunho; `motivo` é a mensagem para o consultor."""

    def __init__(self, motivo: str):
        self.motivo = motivo
        super().__init__(motivo)


@dataclass(frozen=True)
class Resposta:
    texto: str
    modelo: str  # o modelo que de fato respondeu
    alerta: str | None = None  # ex.: resposta cortada


class ProvedorLLM(Protocol):
    nome: str  # "claude", "ollama" ou "falso": vai para o registro do rascunho
    modelo: str  # o modelo configurado

    def redigir(self, pedido: Pedido) -> Resposta: ...


def criar_provedor(
    config: ConfiguracaoLLM, ambiente: Mapping[str, str] | None = None
) -> ProvedorLLM:
    """O provedor escolhido na configuração; LLMIndisponivel se desligado ou sem chave."""
    if config.provedor is Provedor.desligado:
        raise LLMIndisponivel(
            "Os rascunhos por LLM estão desligados. Para ativar, defina "
            "DESCOBERTA_LLM_PROVEDOR no .env (veja o README)."
        )
    if config.provedor is Provedor.claude:
        chave = ler_chave_api(ambiente)
        if chave is None:
            raise LLMIndisponivel(
                "Falta a chave da API: defina ANTHROPIC_API_KEY no .env e reinicie a app."
            )
        from .claude import ProvedorClaude

        return ProvedorClaude(config.claude, chave)
    from .ollama import ProvedorOllama

    return ProvedorOllama(config.ollama)

"""Provedor falso: para os testes e a demonstração, sem rede e sem custo.

Guarda cada pedido recebido (os testes conferem o que sairia) e responde um texto fixo,
calculado a partir do pedido, ou uma falha.
"""

from collections.abc import Callable

from .prompts import Pedido
from .provedor import LLMIndisponivel, Resposta

RESPOSTA_PADRAO = "Rascunho de teste para [CLIENTE], da [EMPRESA]."


class ProvedorFalso:
    nome = "falso"

    def __init__(
        self,
        resposta: str | Callable[[Pedido], str] = RESPOSTA_PADRAO,
        modelo: str = "falso-1",
        erro: LLMIndisponivel | None = None,
    ):
        self._resposta = resposta
        self.modelo = modelo
        self._erro = erro
        self.pedidos: list[Pedido] = []

    def redigir(self, pedido: Pedido) -> Resposta:
        self.pedidos.append(pedido)
        if self._erro is not None:
            raise self._erro
        texto = self._resposta(pedido) if callable(self._resposta) else self._resposta
        return Resposta(texto, self.modelo)

"""Geração de um rascunho: anonimizar, conferir, enviar e desfazer, nesta ordem.

1. O pedido (instruções e mensagem) passa pela anonimização.
2. Conferência final: se algo ainda parecer dado pessoal, o pedido não sai.
3. O provedor responde (ou levanta LLMIndisponivel, que passa adiante: nada é gravado).
4. Os marcadores da resposta voltam a ser os dados reais, aqui na máquina.

`previa_do_pedido` mostra ao consultor exatamente o que sairia, sem enviar nada.
"""

import re
from dataclasses import dataclass

from .anonimizacao import Anonimizador
from .prompts import Pedido
from .provedor import LLMIndisponivel, ProvedorLLM

PEDIDO_COM_DADOS = (
    "O pedido ainda tinha dados pessoais depois da anonimização e não foi enviado: {}."
)


@dataclass(frozen=True)
class RascunhoGerado:
    texto: str  # já com os dados reais de volta
    provedor: str
    modelo: str
    versao_prompt: str
    alertas: tuple[str, ...] = ()


@dataclass(frozen=True)
class Previa:
    pedido: Pedido  # exatamente o que sai
    substituicoes: dict[str, str]  # marcador → valor real, só os usados no pedido


def _anonimizar(pedido: Pedido, anonimizador: Anonimizador) -> Pedido:
    enviado = Pedido(
        anonimizador.anonimizar(pedido.sistema), anonimizador.anonimizar(pedido.mensagem)
    )
    sobras = anonimizador.restantes(f"{enviado.sistema}\n{enviado.mensagem}")
    if sobras:
        raise LLMIndisponivel(PEDIDO_COM_DADOS.format(len(sobras)))
    return enviado


def previa_do_pedido(pedido: Pedido, anonimizador: Anonimizador) -> Previa:
    enviado = _anonimizar(pedido, anonimizador)
    texto = f"{enviado.sistema}\n{enviado.mensagem}"
    usados = {m: v for m, v in anonimizador.substituicoes.items() if m in texto}
    return Previa(enviado, usados)


_PALAVRA = re.compile(r"[^\W\d_]")  # conta só o que tem letra ("1." e "-" de lista, não)


def contar_palavras(texto: str) -> int:
    return sum(1 for pedaco in texto.split() if _PALAVRA.search(pedaco))


def gerar_rascunho(
    provedor: ProvedorLLM,
    versao_prompt: str,
    pedido: Pedido,
    anonimizador: Anonimizador,
    limite_palavras: tuple[int, int] | None = None,
) -> RascunhoGerado:
    """`limite_palavras`: fora da faixa, o rascunho vem com um alerta (não é cortado)."""
    enviado = _anonimizar(pedido, anonimizador)
    resposta = provedor.redigir(enviado)
    desfeito = anonimizador.desfazer(resposta.texto)
    alertas = []
    if desfeito.desconhecidos:
        alertas.append(
            "A resposta trouxe marcadores que não estavam no pedido ("
            + ", ".join(desfeito.desconhecidos)
            + "): confira esses trechos."
        )
    if resposta.alerta:
        alertas.append(resposta.alerta)
    if limite_palavras is not None:
        minimo, maximo = limite_palavras
        palavras = contar_palavras(desfeito.texto)
        if not minimo <= palavras <= maximo:
            alertas.append(
                f"O rascunho tem cerca de {palavras} palavras, fora do tamanho pedido "
                f"({minimo} a {maximo}): ajuste antes de aceitar."
            )
    return RascunhoGerado(
        texto=desfeito.texto,
        provedor=provedor.nome,
        modelo=resposta.modelo,
        versao_prompt=versao_prompt,
        alertas=tuple(alertas),
    )

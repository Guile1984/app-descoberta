"""Atalhos de teclado da sessão ao vivo: a lista única de onde saem a ajuda e o JS.

A página da sessão recebe esta lista duas vezes: como tabela, na tela de ajuda
(Ctrl+/), e como JSON, que o static/atalhos.js lê para saber o que fazer com cada tecla.
Assim a ajuda nunca mostra um atalho diferente do que funciona de verdade.

Teclas: `code` é a tecla física (Digit1, KeyP), igual em qualquer layout de teclado;
`key` é o caractere digitado ("/", "?"), que muda de lugar no teclado ABNT2.
Evitamos Alt+D, Alt+E e Alt+F, que o Chrome e o Edge já usam.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Combinacao:
    code: str | None = None
    key: str | None = None
    alt: bool = False
    ctrl: bool = False
    fora_de_campo: bool = False  # só vale quando o cursor não está num campo de texto
    alvo: str | None = None  # só vale com o cursor neste campo (id do HTML)
    argumento: Any = None  # passado para a ação (ex.: o número do bloco)

    def para_js(self) -> dict[str, Any]:
        """Só os campos preenchidos, para o JSON ficar curto."""
        return {
            nome: valor
            for nome, valor in vars(self).items()
            if valor is not None and valor is not False
        }


@dataclass(frozen=True)
class Atalho:
    acao: str  # nome da função em atalhos.js
    teclas: str  # como aparece na ajuda
    descricao: str
    combinacoes: tuple[Combinacao, ...]

    def para_js(self) -> dict[str, Any]:
        return {"acao": self.acao, "combinacoes": [c.para_js() for c in self.combinacoes]}


def _alt(letra: str) -> tuple[Combinacao, ...]:
    return (Combinacao(code=f"Key{letra}", alt=True),)


ATALHOS = (
    Atalho(
        "ajuda",
        "Ctrl+/ ou ?",
        "Abre e fecha esta ajuda (? só fora de campo de texto)",
        (Combinacao(key="/", ctrl=True), Combinacao(key="?", fora_de_campo=True)),
    ),
    Atalho(
        "bloco",
        "Alt+1 … Alt+9, Alt+0",
        "Vai para o bloco 1 a 9 (Alt+0: bloco 10)",
        tuple(Combinacao(code=f"Digit{n % 10}", alt=True, argumento=n) for n in range(1, 11)),
    ),
    Atalho("encerramento", "Alt+R", "Vai para o encerramento", _alt("R")),
    Atalho(
        "proxima_pendente",
        "Alt+P",
        "Próxima obrigatória sem resposta (passa para o bloco seguinte quando acabam)",
        _alt("P"),
    ),
    Atalho(
        "sinais",
        "Alt+S",
        "Sinais de alerta do bloco: Tab navega, Espaço marca ou desmarca",
        _alt("S"),
    ),
    Atalho("anotacao", "Alt+N", "Escreve uma anotação", _alt("N")),
    Atalho(
        "salvar_anotacao",
        "Ctrl+Enter",
        "Salva a anotação e volta ao campo onde você estava",
        (Combinacao(key="Enter", ctrl=True, alvo="anotacao-texto"),),
    ),
    Atalho("calculos", "Alt+C", "Vai para o painel de cálculos", _alt("C")),
    Atalho("cronometro", "Alt+T", "Inicia, pausa ou retoma o cronômetro", _alt("T")),
    Atalho(
        "voltar_ao_campo",
        "Esc",
        "Volta ao último campo de resposta (na ajuda, Esc fecha a ajuda)",
        (Combinacao(key="Escape"),),
    ),
)


def atalhos_para_js() -> list[dict[str, Any]]:
    return [atalho.para_js() for atalho in ATALHOS]

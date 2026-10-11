"""Markdown: texto puro, sem biblioteca. É também o texto canônico de onde sai o hash."""

import re
from typing import TYPE_CHECKING

from ..documento import (
    Assinatura,
    Aviso,
    Capa,
    Documento,
    Lista,
    Paragrafo,
    QuebraDePagina,
    Tabela,
    Titulo,
)

if TYPE_CHECKING:
    from ..emissao import RelatorioEmitido

# Caracteres que o Markdown interpretaria (negrito, título, HTML, link…).
_ESPECIAIS = re.compile(r"([\\`*_#<>\[\]])")
LINHA_ASSINATURA = "_" * 30


def escapar(texto: str) -> str:
    return _ESPECIAIS.sub(r"\\\1", texto)


def _celula(texto: str) -> str:
    return escapar(texto).replace("|", r"\|").replace("\r\n", "\n").replace("\n", "<br>")


def _tabela(tabela: Tabela) -> str:
    linhas = [
        "| " + " | ".join(_celula(c) for c in tabela.colunas) + " |",
        "|" + "|".join(" --- " for _ in tabela.colunas) + "|",
    ]
    linhas += ["| " + " | ".join(_celula(c) for c in linha) + " |" for linha in tabela.linhas]
    return "\n".join(linhas)


def _bloco(bloco) -> str:
    match bloco:
        case Capa():
            partes = [f"# {escapar(bloco.titulo)}", f"**{escapar(bloco.subtitulo)}**"]
            if bloco.faixa:
                partes.append(f"> **{escapar(bloco.faixa)}**")
            partes.append("\n".join(f"- **{r}:** {escapar(v)}" for r, v in bloco.linhas))
            if bloco.nota:
                partes.append(f"*{escapar(bloco.nota)}*")
            return "\n\n".join(partes)
        case Titulo():
            return ("## " if bloco.nivel == 1 else "### ") + escapar(bloco.texto)
        case Paragrafo():
            texto = escapar(bloco.texto)
            return f"**{escapar(bloco.rotulo)}** {texto}" if bloco.rotulo else texto
        case Aviso():
            return f"> {escapar(bloco.texto)}"
        case Lista():
            return "\n".join(f"- {escapar(item)}" for item in bloco.itens)
        case Tabela():
            return _tabela(bloco)
        case Assinatura():
            campos = [f"**{campo}:** {LINHA_ASSINATURA}" for campo in bloco.campos]
            return "\n\n".join([f"**{escapar(bloco.titulo)}**", *campos])
        case QuebraDePagina():
            return "---"
    raise TypeError(f"bloco desconhecido: {bloco!r}")


def markdown_do_documento(documento: Documento) -> str:
    return "\n\n".join(_bloco(bloco) for bloco in documento.blocos) + "\n"


def exportar_markdown(emitido: "RelatorioEmitido") -> str:
    """O texto canônico mais o rodapé no fim (o rodapé tem o hash, por isso fica de fora
    do texto que é resumido pelo hash)."""
    return f"{emitido.markdown}\n---\n\n{emitido.rodape}\n"

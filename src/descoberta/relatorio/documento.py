"""O relatório como um documento neutro: uma lista de blocos simples.

A montagem (`montagem.py`) decide o conteúdo; os exportadores (Markdown, DOCX, PDF e a
prévia em HTML) só desenham cada tipo de bloco. Assim os formatos nunca divergem: o que
entra em cada versão do relatório é decidido num lugar só.
"""

from dataclasses import dataclass, field
from typing import ClassVar

# Marca de conteúdo que ainda falta preencher (aparece no lugar do texto ou valor).
FALTA = "⚠ A preencher"


@dataclass(frozen=True)
class Capa:
    tipo: ClassVar[str] = "capa"
    titulo: str
    subtitulo: str
    linhas: list[tuple[str, str]]  # (rótulo, valor)
    faixa: str | None = None  # destaque no topo (ex.: "USO INTERNO")
    nota: str | None = None  # frase de confidencialidade
    # PNG do perfil do consultor. Vai no PDF, no Word e na prévia; o Markdown não tem
    # imagem, então o logotipo não entra no texto canônico (nem no hash do rodapé).
    logotipo: bytes | None = None


@dataclass(frozen=True)
class Titulo:
    tipo: ClassVar[str] = "titulo"
    texto: str
    nivel: int = 1  # 1: seção ou anexo; 2: subtítulo


@dataclass(frozen=True)
class Paragrafo:
    tipo: ClassVar[str] = "paragrafo"
    texto: str
    rotulo: str | None = None  # começo em negrito ("Tipo de solução: …")


@dataclass(frozen=True)
class Aviso:
    """Texto em destaque: pendência, hipótese, aviso de que não é contrato."""

    tipo: ClassVar[str] = "aviso"
    texto: str


@dataclass(frozen=True)
class Lista:
    tipo: ClassVar[str] = "lista"
    itens: list[str]


@dataclass(frozen=True)
class Tabela:
    tipo: ClassVar[str] = "tabela"
    colunas: list[str]
    linhas: list[list[str]]
    # Nível ("baixo", "medio", "alto") de cada célula, para colorir a matriz de riscos.
    niveis: list[list[str | None]] | None = None
    larguras: list[float] | None = None  # proporção de cada coluna (soma qualquer)


@dataclass(frozen=True)
class Assinatura:
    tipo: ClassVar[str] = "assinatura"
    titulo: str  # "Pelo cliente — Construtora Alvorada"
    campos: tuple[str, ...] = ("Nome", "Cargo", "Data", "Assinatura")
    # Campos já preenchidos (ex.: nome do consultor, vindo do perfil); os outros ficam
    # com a linha em branco para preencher à mão.
    valores: tuple[tuple[str, str], ...] = ()

    def valor(self, campo: str) -> str | None:
        return dict(self.valores).get(campo)


@dataclass(frozen=True)
class QuebraDePagina:
    tipo: ClassVar[str] = "quebra"


Bloco = Capa | Titulo | Paragrafo | Aviso | Lista | Tabela | Assinatura | QuebraDePagina


@dataclass(frozen=True)
class Documento:
    titulo: str
    blocos: list[Bloco] = field(default_factory=list)

    def texto(self) -> str:
        """Todo o texto do documento, para buscas nos testes."""
        partes: list[str] = []
        for bloco in self.blocos:
            match bloco:
                case Capa():
                    partes += [bloco.titulo, bloco.subtitulo, bloco.faixa or "", bloco.nota or ""]
                    partes += [f"{rotulo}: {valor}" for rotulo, valor in bloco.linhas]
                case Titulo() | Aviso():
                    partes.append(bloco.texto)
                case Paragrafo():
                    partes.append(f"{bloco.rotulo or ''} {bloco.texto}")
                case Lista():
                    partes += bloco.itens
                case Tabela():
                    partes.append(" | ".join(bloco.colunas))
                    partes += [" | ".join(linha) for linha in bloco.linhas]
                case Assinatura():
                    partes += [bloco.titulo, *bloco.campos, *(v for _, v in bloco.valores)]
        return "\n".join(partes)

    def titulos(self, nivel: int = 1) -> list[str]:
        return [b.texto for b in self.blocos if isinstance(b, Titulo) and b.nivel == nivel]

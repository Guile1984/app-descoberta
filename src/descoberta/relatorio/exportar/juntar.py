"""Vários PDFs num arquivo só (relatório + proposta), com pypdf: Python puro, offline.

As páginas são copiadas como estão: cada parte mantém o próprio rodapé (versão, data,
hash e "Página X de Y"), então a cópia assinada continua conferível parte por parte. O
arquivo junto não é registrado; as partes já são.
"""

import io
from collections.abc import Sequence
from dataclasses import dataclass

from pypdf import PdfReader, PdfWriter


@dataclass(frozen=True)
class Parte:
    titulo: str  # vira um marcador (sumário lateral do leitor de PDF)
    pdf: bytes


def juntar_pdfs(titulo: str, partes: Sequence[Parte]) -> bytes:
    if not partes:
        raise ValueError("é preciso ao menos uma parte para juntar")
    escritor = PdfWriter()
    for parte in partes:
        inicio = len(escritor.pages)
        for pagina in PdfReader(io.BytesIO(parte.pdf)).pages:
            escritor.add_page(pagina)
        escritor.add_outline_item(parte.titulo, inicio)
    escritor.add_metadata({"/Title": titulo, "/Author": "App de Descoberta"})
    saida = io.BytesIO()
    escritor.write(saida)
    return saida.getvalue()

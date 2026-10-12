"""Relatório e proposta num PDF só: cada parte com o próprio rodapé, versão e hash."""

import io

import pytest
from pypdf import PdfReader

from descoberta.relatorio import emitir, emitir_proposta, exportar_pdf
from descoberta.relatorio.exportar.juntar import Parte, juntar_pdfs


@pytest.fixture
def pdfs(dados_roberto, emissao_cliente, dados_proposta_roberto, emissao_proposta):
    relatorio = exportar_pdf(emitir(dados_roberto, emissao_cliente))
    proposta = exportar_pdf(emitir_proposta(dados_proposta_roberto, emissao_proposta))
    return relatorio, proposta


def _paginas(dados: bytes) -> int:
    return len(PdfReader(io.BytesIO(dados)).pages)


def test_paginas_das_duas_partes_na_ordem(pdfs):
    relatorio, proposta = pdfs
    junto = juntar_pdfs(
        "Relatório e proposta", [Parte("Relatório", relatorio), Parte("Proposta", proposta)]
    )
    leitor = PdfReader(io.BytesIO(junto))
    assert len(leitor.pages) == _paginas(relatorio) + _paginas(proposta)
    primeira_da_proposta = leitor.pages[_paginas(relatorio)].extract_text()
    assert "Proposta · Rascunho" in primeira_da_proposta
    assert "Página 1 de" in primeira_da_proposta  # cada parte mantém a própria numeração
    assert "Rascunho não registrado (cliente)" in leitor.pages[0].extract_text()


def test_marcadores_e_titulo(pdfs):
    relatorio, proposta = pdfs
    junto = juntar_pdfs("Pacote", [Parte("Relatório", relatorio), Parte("Proposta", proposta)])
    leitor = PdfReader(io.BytesIO(junto))
    assert [m.title for m in leitor.outline] == ["Relatório", "Proposta"]
    assert leitor.get_destination_page_number(leitor.outline[1]) == _paginas(relatorio)
    assert leitor.metadata.title == "Pacote"


def test_sem_partes():
    with pytest.raises(ValueError, match="parte"):
        juntar_pdfs("Vazio", [])

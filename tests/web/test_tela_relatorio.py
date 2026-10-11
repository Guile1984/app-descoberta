"""Página do relatório: prévia, downloads, versões registradas e hipóteses na revisão."""

import hashlib
import io

import pytest
from pypdf import PdfReader

from descoberta.repositorio import hipoteses_da_sessao, salvar_texto_secao, versoes_da_sessao

HX = {"HX-Request": "true"}

# --- Página ---


def test_links_para_o_relatorio(cliente_http, sessao):
    url = f'href="/sessoes/{sessao.id}/relatorio"'
    assert url in cliente_http.get(f"/sessoes/{sessao.id}").text
    assert url in cliente_http.get(f"/sessoes/{sessao.id}/revisao").text


def test_pagina_do_relatorio_do_roberto(cliente_demo):
    cliente, sessao_id = cliente_demo
    resposta = cliente.get(f"/sessoes/{sessao_id}/relatorio")
    assert resposta.status_code == 200
    html = resposta.text
    assert "Relatório de Descoberta" in html
    assert "1. Resumo executivo" in html
    assert "7,7 meses" in html
    assert "Termo de ciência e validação" in html
    assert "Anexo C" not in html  # prévia da versão cliente
    for formato in ("md", "docx", "pdf"):
        assert f'href="/sessoes/{sessao_id}/relatorio.{formato}?versao=cliente"' in html
    assert "Nenhuma versão registrada" in html


def test_previa_da_versao_interna(cliente_demo):
    cliente, sessao_id = cliente_demo
    html = cliente.get(f"/sessoes/{sessao_id}/relatorio?versao=interna").text
    assert "Anexo C — Uso interno" in html
    assert "USO INTERNO" in html
    assert f'href="/sessoes/{sessao_id}/relatorio.pdf?versao=interna"' in html


def test_versao_inexistente_da_404(cliente_demo):
    cliente, sessao_id = cliente_demo
    assert cliente.get(f"/sessoes/{sessao_id}/relatorio?versao=publica").status_code == 404
    assert cliente.get(f"/sessoes/{sessao_id}/relatorio.pdf?versao=publica").status_code == 404


def test_sessao_vazia_avisa_o_que_falta(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}/relatorio").text
    assert "trechos a preencher" in html
    assert f'href="/sessoes/{sessao.id}/revisao"' in html


def test_texto_do_cliente_e_escapado_na_previa(cliente_http, banco, sessao):
    salvar_texto_secao(banco, sessao.id, "resumo_executivo", "<script>alert(1)</script>")
    html = cliente_http.get(f"/sessoes/{sessao.id}/relatorio").text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


# --- Downloads (rascunho, sem registrar) ---


@pytest.mark.parametrize(
    ("formato", "tipo", "inicio"),
    [
        ("md", "text/markdown; charset=utf-8", b"# Relat"),
        ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK"),
        ("pdf", "application/pdf", b"%PDF"),
    ],
)
def test_download_nos_tres_formatos(cliente_demo, formato, tipo, inicio):
    cliente, sessao_id = cliente_demo
    resposta = cliente.get(f"/sessoes/{sessao_id}/relatorio.{formato}?versao=cliente")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == tipo
    assert resposta.content.startswith(inicio)
    disposicao = resposta.headers["content-disposition"]
    assert "attachment" in disposicao
    assert f"relatorio-descoberta-construtora-alvorada-2026-10-07-cliente.{formato}" in disposicao


def test_download_nao_registra_versao(cliente_demo):
    cliente, sessao_id = cliente_demo
    cliente.get(f"/sessoes/{sessao_id}/relatorio.pdf?versao=cliente")
    assert "Nenhuma versão registrada" in cliente.get(f"/sessoes/{sessao_id}/relatorio").text


def test_rascunho_avisa_no_rodape(cliente_demo):
    cliente, sessao_id = cliente_demo
    pdf = cliente.get(f"/sessoes/{sessao_id}/relatorio.pdf?versao=cliente").content
    primeira = PdfReader(io.BytesIO(pdf)).pages[0].extract_text()
    assert "Rascunho não registrado (cliente)" in primeira


def test_formato_inexistente_da_404(cliente_demo):
    cliente, sessao_id = cliente_demo
    assert cliente.get(f"/sessoes/{sessao_id}/relatorio.odt?versao=cliente").status_code == 404


# --- Versões registradas ---


def _registrar(cliente, sessao_id, versao="cliente"):
    return cliente.post(f"/sessoes/{sessao_id}/relatorio/versoes", data={"versao": versao})


def test_registrar_versao_enviada(cliente_demo, app_demo_banco):
    cliente, sessao_id = cliente_demo
    resposta = _registrar(cliente, sessao_id)
    assert resposta.status_code == 303
    assert resposta.headers["location"] == f"/sessoes/{sessao_id}/relatorio?versao=cliente#versoes"

    [versao] = versoes_da_sessao(app_demo_banco(), sessao_id)
    assert (versao.numero, versao.tipo) == (1, "cliente")
    assert versao.hash_pdf == hashlib.sha256(versao.pdf).hexdigest()
    assert versao.hash_conteudo == hashlib.sha256(versao.conteudo_md.encode()).hexdigest()
    # O rodapé de cada página mostra a versão, a data e o começo do hash do conteúdo.
    for pagina in PdfReader(io.BytesIO(versao.pdf)).pages:
        texto = pagina.extract_text()
        assert "Versão 1 (cliente), emitida em" in texto
        assert versao.hash_conteudo[:12] in texto


def test_versoes_numeradas_e_listadas_com_download(cliente_demo):
    cliente, sessao_id = cliente_demo
    _registrar(cliente, sessao_id)
    _registrar(cliente, sessao_id, "interna")
    html = cliente.get(f"/sessoes/{sessao_id}/relatorio").text
    assert f'href="/sessoes/{sessao_id}/relatorio/versoes/2.pdf"' in html
    assert f'href="/sessoes/{sessao_id}/relatorio/versoes/1.pdf"' in html
    assert html.index("/versoes/2.pdf") < html.index("/versoes/1.pdf")  # mais recente primeiro
    assert "Interna" in html


def test_download_da_versao_registrada_devolve_o_pdf_guardado(cliente_demo, app_demo_banco):
    cliente, sessao_id = cliente_demo
    _registrar(cliente, sessao_id)
    [versao] = versoes_da_sessao(app_demo_banco(), sessao_id)
    resposta = cliente.get(f"/sessoes/{sessao_id}/relatorio/versoes/1.pdf")
    assert resposta.status_code == 200
    assert resposta.content == versao.pdf  # o mesmo arquivo, sem gerar de novo
    assert (
        "relatorio-descoberta-construtora-alvorada-2026-10-07-cliente-v1.pdf"
        in (resposta.headers["content-disposition"])
    )


def test_versao_registrada_inexistente_da_404(cliente_demo):
    cliente, sessao_id = cliente_demo
    assert cliente.get(f"/sessoes/{sessao_id}/relatorio/versoes/9.pdf").status_code == 404


def test_registrar_versao_invalida_da_404(cliente_demo, app_demo_banco):
    cliente, sessao_id = cliente_demo
    assert _registrar(cliente, sessao_id, "publica").status_code == 404
    assert versoes_da_sessao(app_demo_banco(), sessao_id) == []


# --- Hipóteses na revisão ---


def test_revisao_mostra_as_hipoteses_dos_calculos(cliente_demo):
    cliente, sessao_id = cliente_demo
    html = cliente.get(f"/sessoes/{sessao_id}/revisao").text
    assert 'id="hipoteses"' in html
    assert 'id="hipotese-custo_hora"' in html
    assert "R$ 100,00" in html
    assert 'id="hipotese-custo_hora" name="valor" value="sim" checked' in html
    assert 'id="hipotese-investimento" name="valor" value="sim" hx-post' in html


def test_marcar_e_desmarcar_hipotese(cliente_http, banco, sessao):
    url = f"/sessoes/{sessao.id}/hipoteses/custo_hora"
    resposta = cliente_http.post(url, data={"valor": "sim"}, headers=HX)
    assert resposta.status_code == 200
    assert "Salvo às" in resposta.text
    banco.expire_all()
    assert hipoteses_da_sessao(banco, sessao.id) == {"custo_hora"}
    cliente_http.post(url, data={}, headers=HX)  # caixa desmarcada: o navegador não envia nada
    banco.expire_all()
    assert hipoteses_da_sessao(banco, sessao.id) == set()


def test_hipotese_de_campo_inexistente_da_404(cliente_http, sessao):
    resposta = cliente_http.post(f"/sessoes/{sessao.id}/hipoteses/frequencia_periodo")
    assert resposta.status_code == 404

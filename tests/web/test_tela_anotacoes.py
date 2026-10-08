"""Anotações livres: criar, editar e excluir sem sair da sessão."""

from descoberta.repositorio import adicionar_anotacao, anotacoes_da_sessao

HX = {"HX-Request": "true"}


def _anotacoes(banco, sessao_id):
    banco.expire_all()
    return anotacoes_da_sessao(banco, sessao_id)


def test_formulario_ja_vem_ligado_ao_bloco_aberto(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=4").text
    assert 'id="anotacao-texto"' in html
    assert 'id="anotacao-bloco" name="bloco" value="4"' in html


def test_criar_anotacao_no_bloco(cliente_http, banco, sessao):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/anotacoes",
        data={"texto": "Marcos parece cético.", "bloco": "2"},
        headers=HX,
    )
    assert resposta.status_code == 200
    assert "<html" not in resposta.text
    assert "Marcos parece cético." in resposta.text
    [anotacao] = _anotacoes(banco, sessao.id)
    assert (anotacao.texto, anotacao.bloco) == ("Marcos parece cético.", 2)


def test_anotacao_geral_sem_bloco(cliente_http, banco, sessao):
    cliente_http.post(f"/sessoes/{sessao.id}/anotacoes", data={"texto": "Geral", "bloco": ""})
    assert _anotacoes(banco, sessao.id)[0].bloco is None


def test_anotacao_vazia_e_recusada_e_o_texto_nao_some(cliente_http, banco, sessao):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/anotacoes", data={"texto": "   ", "bloco": "1"}, headers=HX
    )
    assert resposta.status_code == 422
    assert "Não salvo" in resposta.text
    assert _anotacoes(banco, sessao.id) == []


def test_lista_mostra_a_mais_recente_primeiro_com_hora_e_bloco(cliente_http, banco, sessao):
    adicionar_anotacao(banco, sessao.id, "Primeira", bloco=1)
    adicionar_anotacao(banco, sessao.id, "Segunda")
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert html.index("Segunda") < html.index("Primeira")
    assert "Bloco 1" in html
    assert "Geral" in html


def test_editar_anotacao(cliente_http, banco, sessao):
    anotacao = adicionar_anotacao(banco, sessao.id, "Rascunho", bloco=1)
    formulario = cliente_http.get(
        f"/sessoes/{sessao.id}/anotacoes/{anotacao.id}/editar", headers=HX
    ).text
    assert "<textarea" in formulario
    assert "Rascunho" in formulario
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/anotacoes/{anotacao.id}", data={"texto": "Final"}, headers=HX
    )
    assert resposta.status_code == 200
    assert "Final" in resposta.text
    assert _anotacoes(banco, sessao.id)[0].texto == "Final"


def test_cancelar_edicao_mostra_a_anotacao_de_novo(cliente_http, banco, sessao):
    anotacao = adicionar_anotacao(banco, sessao.id, "Como estava")
    html = cliente_http.get(f"/sessoes/{sessao.id}/anotacoes/{anotacao.id}", headers=HX).text
    assert "Como estava" in html
    assert "<textarea" not in html


def test_edicao_vazia_e_recusada(cliente_http, banco, sessao):
    anotacao = adicionar_anotacao(banco, sessao.id, "Original")
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/anotacoes/{anotacao.id}", data={"texto": ""}, headers=HX
    )
    assert resposta.status_code == 422
    assert _anotacoes(banco, sessao.id)[0].texto == "Original"


def test_excluir_anotacao(cliente_http, banco, sessao):
    anotacao = adicionar_anotacao(banco, sessao.id, "Apagar")
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/anotacoes/{anotacao.id}/excluir", headers=HX
    )
    assert resposta.status_code == 200
    assert resposta.text == ""
    assert _anotacoes(banco, sessao.id) == []


def test_anotacao_de_outra_sessao_da_404(cliente_http, banco, cliente, sessao):
    from datetime import date

    from descoberta.repositorio import criar_sessao

    outra = criar_sessao(
        banco, cliente_id=cliente.id, data=date(2026, 10, 8), versao_questionario=1
    )
    anotacao = adicionar_anotacao(banco, outra.id, "De outra sessão")
    url = f"/sessoes/{sessao.id}/anotacoes/{anotacao.id}"
    assert cliente_http.post(url, data={"texto": "x"}).status_code == 404
    assert cliente_http.post(f"{url}/excluir").status_code == 404
    assert _anotacoes(banco, outra.id)[0].texto == "De outra sessão"


def test_anotacao_e_escapada(cliente_http, banco, sessao):
    adicionar_anotacao(banco, sessao.id, "<script>alert(1)</script>")
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert "<script>alert(1)</script>" not in html

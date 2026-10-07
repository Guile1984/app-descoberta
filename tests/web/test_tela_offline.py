"""A app precisa funcionar sem internet: nada pode ser carregado de fora do notebook."""

import re

URL_EXTERNA = re.compile(r"""(?:src|href)=["'](?:https?:)?//""")


def test_paginas_so_usam_arquivos_locais(cliente_http, cliente, sessao):
    for caminho in ("/", f"/clientes/{cliente.id}", f"/sessoes/{sessao.id}", "/clientes/novo"):
        html = cliente_http.get(caminho).text
        assert not URL_EXTERNA.search(html), caminho
        assert 'src="/static/htmx.min.js"' in html


def test_htmx_e_servido_pela_propria_app(cliente_http):
    resposta = cliente_http.get("/static/htmx.min.js")
    assert resposta.status_code == 200
    assert 'version:"2.0.4"' in resposta.text


def test_historico_do_htmx_nao_guarda_paginas_no_navegador(cliente_http):
    # Sem cópia das páginas (com dados de clientes) no armazenamento do navegador; o botão
    # "voltar" busca a página de novo no servidor.
    html = cliente_http.get("/").text
    assert '"historyCacheSize":0' in html.replace(" ", "")
    assert '"refreshOnHistoryMiss":true' in html.replace(" ", "")


def test_erro_de_validacao_mostra_a_mensagem_do_servidor(cliente_http):
    # Por padrão, o HTMX ignora respostas de erro. O 422 traz a mensagem "Não salvo: …"
    # que deve aparecer no aviso do campo; os demais erros ficam com o aviso genérico.
    html = cliente_http.get("/").text.replace(" ", "")
    assert '{"code":"422","swap":true,"error":true}' in html

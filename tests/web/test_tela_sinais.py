"""Sinais de alerta marcados com um clique (ou Espaço), na coluna da direita."""

from descoberta.repositorio import marcar_sinal, sinais_marcados

HX = {"HX-Request": "true"}


def _marcar(cliente_http, sessao_id, sinal_id, marcar="1"):
    return cliente_http.post(
        f"/sessoes/{sessao_id}/sinais/{sinal_id}", data={"marcar": marcar}, headers=HX
    )


def _ids(banco, sessao_id):
    banco.expire_all()
    return [s.sinal_id for s in sinais_marcados(banco, sessao_id)]


def test_coluna_da_direita_mostra_os_sinais_do_bloco_aberto(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=2").text
    assert 'id="sinais"' in html
    assert f'hx-post="/sessoes/{sessao.id}/sinais/b2.s1"' in html
    assert f'hx-post="/sessoes/{sessao.id}/sinais/b1.s1"' not in html


def test_marcar_devolve_o_botao_pressionado_e_avisa_os_calculos(cliente_http, banco, sessao):
    resposta = _marcar(cliente_http, sessao.id, "b2.s3")
    assert resposta.status_code == 200
    assert 'aria-pressed="true"' in resposta.text
    assert "<html" not in resposta.text
    assert "sinais-mudaram" in resposta.headers["HX-Trigger"]
    assert _ids(banco, sessao.id) == ["b2.s3"]


def test_marcar_duas_vezes_nao_duplica_e_desmarcar_apaga(cliente_http, banco, sessao):
    _marcar(cliente_http, sessao.id, "b2.s3")
    _marcar(cliente_http, sessao.id, "b2.s3")
    assert _ids(banco, sessao.id) == ["b2.s3"]
    resposta = _marcar(cliente_http, sessao.id, "b2.s3", marcar="0")
    assert 'aria-pressed="false"' in resposta.text
    assert _ids(banco, sessao.id) == []


def test_botao_pede_o_estado_oposto_ao_atual(cliente_http, banco, sessao):
    # O botão manda o estado desejado (e não "inverta"): dois pedidos repetidos dão o mesmo
    # resultado, sem marcar e desmarcar por engano.
    marcar_sinal(banco, sessao.id, "b2.s3")
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=2").text
    assert '"marcar": "0"' in html  # b2.s3 marcado: clicar desmarca
    assert '"marcar": "1"' in html  # os outros: clicar marca


def test_sinal_inexistente_da_404(cliente_http, banco, sessao):
    assert _marcar(cliente_http, sessao.id, "b2.s99").status_code == 404
    assert _ids(banco, sessao.id) == []


def test_observacao_do_sinal_marcado(cliente_http, banco, sessao):
    _marcar(cliente_http, sessao.id, "b9.s1")
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/sinais/b9.s1/observacao",
        data={"valor": "Roberto não quis falar em valores."},
        headers=HX,
    )
    assert resposta.status_code == 200
    assert "Salvo às" in resposta.text
    banco.expire_all()
    [sinal] = sinais_marcados(banco, sessao.id)
    assert sinal.observacao == "Roberto não quis falar em valores."
    cliente_http.post(f"/sessoes/{sessao.id}/sinais/b9.s1/observacao", data={"valor": ""})
    banco.expire_all()
    assert sinais_marcados(banco, sessao.id)[0].observacao is None


def test_observacao_de_sinal_nao_marcado_e_recusada(cliente_http, sessao):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/sinais/b9.s1/observacao", data={"valor": "x"}, headers=HX
    )
    assert resposta.status_code == 422
    assert "Não salvo" in resposta.text


def test_texto_do_sinal_e_escapado(cliente_http, banco, sessao):
    marcar_sinal(banco, sessao.id, "b2.s3", observacao="<b>forte</b>")
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=2").text
    assert "<b>forte</b>" not in html
    assert "&lt;b&gt;forte&lt;/b&gt;" in html

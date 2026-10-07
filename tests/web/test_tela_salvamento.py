"""Salvamento automático das respostas, uma pergunta por vez."""

from descoberta.repositorio import atualizar_sessao, respostas_da_sessao, salvar_resposta

HX = {"HX-Request": "true"}


def _salvar(cliente_http, sessao_id, pergunta_id, texto):
    return cliente_http.post(
        f"/sessoes/{sessao_id}/respostas/{pergunta_id}", data={"texto": texto}, headers=HX
    )


def test_resposta_salva_devolve_so_o_aviso(cliente_http, banco, sessao):
    resposta = _salvar(cliente_http, sessao.id, "b1.o1", "Chamados de fissura.")
    assert resposta.status_code == 200
    assert "Salvo às" in resposta.text
    assert "<html" not in resposta.text  # só o pedacinho de HTML do aviso
    assert "<textarea" not in resposta.text  # o campo não é redesenhado (cursor fica onde está)
    assert respostas_da_sessao(banco, sessao.id) == {"b1.o1": "Chamados de fissura."}


def test_resposta_reaparece_ao_recarregar(cliente_http, sessao):
    _salvar(cliente_http, sessao.id, "b1.o2", "Cerca de 15 por mês.")
    assert "Cerca de 15 por mês." in cliente_http.get(f"/sessoes/{sessao.id}").text


def test_salvar_de_novo_atualiza(cliente_http, banco, sessao):
    _salvar(cliente_http, sessao.id, "b1.o1", "Primeira versão")
    _salvar(cliente_http, sessao.id, "b1.o1", "Segunda versão")
    assert respostas_da_sessao(banco, sessao.id) == {"b1.o1": "Segunda versão"}


def test_apagar_o_texto_apaga_a_resposta(cliente_http, banco, sessao):
    _salvar(cliente_http, sessao.id, "b1.o1", "Algo")
    resposta = _salvar(cliente_http, sessao.id, "b1.o1", "")
    assert resposta.status_code == 200
    assert respostas_da_sessao(banco, sessao.id) == {}


def test_pergunta_inexistente_no_questionario_da_404(cliente_http, banco, sessao):
    # Pendência do Sprint 3: o id precisa existir no questionário da versão da sessão.
    resposta = _salvar(cliente_http, sessao.id, "b1.o99", "Texto")
    assert resposta.status_code == 404
    assert respostas_da_sessao(banco, sessao.id) == {}


def test_condicional_invisivel_nao_aceita_resposta(cliente_http, banco, sessao):
    resposta = _salvar(cliente_http, sessao.id, "b4.vc1", "O mestre de obras, no celular.")
    assert resposta.status_code == 422
    assert "Não salvo" in resposta.text
    assert respostas_da_sessao(banco, sessao.id) == {}


def test_sessao_inexistente_da_404(cliente_http):
    assert _salvar(cliente_http, 999, "b1.o1", "Texto").status_code == 404


def test_texto_com_html_e_mostrado_sem_executar(cliente_http, banco, sessao):
    salvar_resposta(banco, sessao.id, "b1.o1", "<script>alert(1)</script>")
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_campo_da_resposta_aponta_para_o_proprio_aviso(cliente_http, banco, sessao):
    atualizar_sessao(banco, sessao.id, tipo_solucao="visao_computacional")
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=4", headers=HX).text
    # O ponto do id ("b4.vc1") vira hífen no id do HTML: "#aviso-b4.vc1" seria lido pelo
    # navegador como "elemento aviso-b4 com a classe vc1".
    assert f'hx-post="/sessoes/{sessao.id}/respostas/b4.vc1"' in html
    assert 'hx-target="#aviso-b4-vc1"' in html
    assert 'id="aviso-b4-vc1"' in html

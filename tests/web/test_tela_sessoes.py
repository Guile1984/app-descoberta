"""Abertura da sessão, página com abas por bloco e campos da sessão."""

import re

import pytest

from descoberta.repositorio import listar_sessoes, obter_sessao

HX = {"HX-Request": "true"}


def test_nova_sessao_usa_a_versao_mais_recente_do_questionario(cliente_http, banco, cliente):
    resposta = cliente_http.post(f"/clientes/{cliente.id}/sessoes", data={"data": "2026-10-08"})
    assert resposta.status_code == 303
    [sessao] = listar_sessoes(banco, cliente.id)
    assert resposta.headers["location"] == f"/sessoes/{sessao.id}"
    assert sessao.versao_questionario == 1
    assert sessao.data.isoformat() == "2026-10-08"


def test_nova_sessao_com_data_invalida(cliente_http, banco, cliente):
    resposta = cliente_http.post(f"/clientes/{cliente.id}/sessoes", data={"data": "ontem"})
    assert resposta.status_code == 422
    assert listar_sessoes(banco, cliente.id) == []


def test_pagina_da_sessao_tem_as_10_abas_e_abre_no_bloco_1(cliente_http, sessao):
    resposta = cliente_http.get(f"/sessoes/{sessao.id}")
    assert resposta.status_code == 200
    assert "<html" in resposta.text
    for numero in range(1, 11):
        assert f'href="/sessoes/{sessao.id}?bloco={numero}"' in resposta.text
    assert 'aria-current="page"' in resposta.text
    assert "Problema de negócio" in resposta.text
    assert "Construtora Alvorada" in resposta.text


def test_pedido_do_htmx_recebe_so_o_painel_do_bloco(cliente_http, sessao):
    resposta = cliente_http.get(f"/sessoes/{sessao.id}?bloco=4", headers=HX)
    assert resposta.status_code == 200
    assert "<html" not in resposta.text
    assert "Dados" in resposta.text
    assert "b4.o1" in resposta.text


def test_recarregar_a_pagina_mantem_a_aba(cliente_http, sessao):
    # F5 numa aba: pedido normal (sem HX-Request) devolve a página inteira já naquela aba.
    resposta = cliente_http.get(f"/sessoes/{sessao.id}?bloco=4")
    assert "<html" in resposta.text
    assert "b4.o1" in resposta.text
    assert "b1.o1" not in resposta.text


def test_restauracao_do_historico_recebe_a_pagina_inteira(cliente_http, sessao):
    # Botão "voltar" do navegador: o HTMX pede a página inteira com este cabeçalho.
    cabecalhos = HX | {"HX-History-Restore-Request": "true"}
    resposta = cliente_http.get(f"/sessoes/{sessao.id}?bloco=2", headers=cabecalhos)
    assert "<html" in resposta.text


@pytest.mark.parametrize("bloco", [0, 11, "x"])
def test_bloco_inexistente(cliente_http, sessao, bloco):
    assert cliente_http.get(f"/sessoes/{sessao.id}?bloco={bloco}").status_code in {404, 422}


def test_sessao_inexistente_da_404(cliente_http):
    assert cliente_http.get("/sessoes/999").status_code == 404


def test_obrigatorias_antes_e_aprofundamento_recolhido(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=1", headers=HX).text
    inicio_recolhido = html.index("<details")
    assert html.index("b1.o7") < inicio_recolhido < html.index("b1.a1")


def test_bloco_3_mostra_a_escolha_do_tipo_de_solucao(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=3", headers=HX).text
    assert 'name="valor"' in html
    assert "visao_computacional" in html
    assert "Imagens ou vídeo" in html


def test_bloco_10_mostra_as_secoes_do_relatorio(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=10", headers=HX).text
    assert "Recomendação e próximos passos" in html


@pytest.mark.parametrize(
    ("campo", "valor", "esperado"),
    [
        ("status", "em_andamento", "em_andamento"),
        ("contexto_previo", "Indicação de um cliente antigo.", "Indicação de um cliente antigo."),
        ("amostra_dados_recebida", "sim", True),
        ("tipo_solucao", "visao_computacional", "visao_computacional"),
        ("tipo_solucao", "", None),
    ],
)
def test_campos_da_sessao_salvam_sozinhos(cliente_http, banco, sessao, campo, valor, esperado):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/campos/{campo}", data={"valor": valor}, headers=HX
    )
    assert resposta.status_code == 200
    assert "Salvo às" in resposta.text
    banco.expire_all()
    assert getattr(obter_sessao(banco, sessao.id), campo) == esperado


def test_desmarcar_amostra_recebida(cliente_http, banco, sessao):
    # Caixa desmarcada não manda nada no formulário: ausência significa "não".
    cliente_http.post(f"/sessoes/{sessao.id}/campos/amostra_dados_recebida", data={"valor": "sim"})
    cliente_http.post(f"/sessoes/{sessao.id}/campos/amostra_dados_recebida", data={})
    banco.expire_all()
    assert obter_sessao(banco, sessao.id).amostra_dados_recebida is False


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("tipo_solucao", "visao"), ("status", "pausada"), ("versao_questionario", "2")],
)
def test_valores_e_campos_invalidos_sao_recusados(cliente_http, banco, sessao, campo, valor):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/campos/{campo}", data={"valor": valor}, headers=HX
    )
    assert resposta.status_code in {404, 422}
    assert "Não salvo" in resposta.text or resposta.status_code == 404
    banco.expire_all()
    assert obter_sessao(banco, sessao.id).versao_questionario == 1


def test_exclusao_da_sessao_volta_para_o_cliente(cliente_http, banco, cliente, sessao):
    sessao_id, cliente_id = sessao.id, cliente.id  # depois de excluir, o objeto não vale mais
    resposta = cliente_http.post(f"/sessoes/{sessao_id}/excluir", headers=HX)
    assert resposta.headers["HX-Redirect"] == f"/clientes/{cliente_id}"
    banco.expire_all()
    assert obter_sessao(banco, sessao_id) is None


def test_campos_com_salvamento_automatico_mostram_salvando_e_avisam_falha(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=1").text
    campos = re.findall(r"<textarea[^>]*hx-post=[^>]*>", html)
    assert campos
    for campo in campos:
        assert "hx-indicator=" in campo  # "Salvando…" enquanto o pedido está a caminho
        assert "hx-on::after-request=" in campo  # "Não salvo" se o pedido falhar

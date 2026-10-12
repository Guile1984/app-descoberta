"""Rascunhos por LLM na revisão: pessoas citadas, prévia obrigatória, gerar, aceitar, descartar.

O LLM é sempre o provedor falso (criar_app(provedor_llm=...)): nenhum teste chama um
modelo de verdade. Sem provedor injetado, vale config/llm.yaml, que vem desligado.
"""

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from descoberta.demo import popular_demo
from descoberta.llm.falso import ProvedorFalso
from descoberta.llm.provedor import LLMIndisponivel
from descoberta.repositorio import (
    DestinoRascunho,
    SituacaoRascunho,
    alternar_cronometro,
    pessoas_citadas,
    rascunhos_da_sessao,
    textos_da_sessao,
)
from descoberta.web.app import criar_app

RAIZ = Path(__file__).resolve().parents[2]
HX = {"HX-Request": "true"}
RESPOSTA = "Hoje o [PESSOA_1] gasta 60 h por mês; o [CLIENTE] quer responder em 1 dia."


@pytest.fixture
def falso():
    return ProvedorFalso(RESPOSTA)


@pytest.fixture
def montar(tmp_path):
    """App com o demo e o provedor escolhido pelo teste."""
    abertos = []

    def montar(provedor=None):
        caminho = tmp_path / "demo.db"
        sessao_id = popular_demo(caminho, hoje=date(2026, 10, 11))
        app = criar_app(caminho_banco=caminho, pasta_config=RAIZ / "config", provedor_llm=provedor)
        cliente = TestClient(app, follow_redirects=False)
        cliente.__enter__()
        abertos.append(cliente)
        return cliente, sessao_id, app

    yield montar
    for cliente in abertos:
        cliente.__exit__(None, None, None)


@pytest.fixture
def ativo(montar, falso):
    return montar(falso)


def _banco(app) -> Session:
    return Session(app.state.engine)


def _url(sessao_id, resto=""):
    return f"/sessoes/{sessao_id}{resto}"


def _confirmar_previa(cliente, sessao_id):
    previa = cliente.get(_url(sessao_id, "/llm/previa?pagina=revisao"), headers=HX)
    impressao = previa.text.split('name="impressao" value="')[1].split('"')[0]
    resposta = cliente.post(
        _url(sessao_id, "/llm/previa"), data={"impressao": impressao}, headers=HX
    )
    assert resposta.status_code == 200
    return resposta


def _gerar(cliente, sessao_id, texto_id="frase_problema", **dados):
    return cliente.post(
        _url(sessao_id, f"/revisao/textos/{texto_id}/rascunho"), data=dados, headers=HX
    )


# --- Painel ---


def test_painel_com_o_llm_desligado(montar):
    cliente, sessao_id, _ = montar()
    html = cliente.get(_url(sessao_id, "/revisao")).text
    assert "Rascunhos por LLM" in html
    assert "desligados" in html
    assert "DESCOBERTA_LLM_PROVEDOR" in html


def test_opcao_de_anotacoes_internas_desligada_e_com_aviso(ativo):
    cliente, sessao_id, _ = ativo
    html = cliente.get(_url(sessao_id, "/revisao")).text
    assert 'id="anotacoes-internas"' in html
    caixa = html.split('id="anotacoes-internas"')[1].split(">")[0]
    assert "checked" not in caixa
    assert "Usar anotações internas como contexto" in html
    assert "pode aparecer no texto gerado" in html


def test_painel_mostra_o_provedor_e_as_pessoas(ativo):
    cliente, sessao_id, _ = ativo
    html = cliente.get(_url(sessao_id, "/revisao")).text
    assert "falso · falso-1" in html
    assert "Marcos" in html  # na lista do demo
    assert 'value="Cida"' in html  # sugestão, ainda fora da lista


# --- Pessoas citadas ---


def test_incluir_e_remover_pessoa(ativo):
    cliente, sessao_id, app = ativo
    resposta = cliente.post(
        _url(sessao_id, "/llm/pessoas"), data={"nome": "Cida", "pagina": "revisao"}, headers=HX
    )
    assert resposta.status_code == 200
    with _banco(app) as banco:
        pessoas = pessoas_citadas(banco, sessao_id)
    assert [p.nome for p in pessoas] == ["Marcos", "Cida"]
    cliente.post(_url(sessao_id, f"/llm/pessoas/{pessoas[1].id}/remover"), headers=HX)
    with _banco(app) as banco:
        assert [p.nome for p in pessoas_citadas(banco, sessao_id)] == ["Marcos"]


def test_pessoa_invalida(ativo):
    cliente, sessao_id, _ = ativo
    resposta = cliente.post(_url(sessao_id, "/llm/pessoas"), data={"nome": " "}, headers=HX)
    assert resposta.status_code == 422
    assert "nome" in resposta.text


# --- Prévia ---


def test_previa_mostra_o_que_sai_e_as_substituicoes(ativo):
    cliente, sessao_id, _ = ativo
    html = cliente.get(_url(sessao_id, "/llm/previa?pagina=revisao"), headers=HX).text
    pedido = html.split('<pre class="previa-pedido">')[1].split("</pre>")[0]
    assert "[CLIENTE]" in pedido
    assert "[EMPRESA]" in pedido
    assert "Roberto" not in pedido
    assert "Construtora Alvorada" not in pedido
    assert "Anotações do consultor" not in pedido
    # As substituições são mostradas só aqui, na máquina do consultor.
    assert "Roberto" in html
    assert 'name="impressao"' in html


def test_previa_com_anotacoes_internas(ativo):
    cliente, sessao_id, _ = ativo
    html = cliente.get(_url(sessao_id, "/llm/previa?pagina=revisao&anotacoes=1"), headers=HX).text
    assert "Anotações do consultor (uso interno)" in html


def test_previa_vale_ate_a_lista_mudar(ativo):
    cliente, sessao_id, _ = ativo
    assert "Prévia confirmada" in _confirmar_previa(cliente, sessao_id).text
    cliente.post(_url(sessao_id, "/llm/pessoas"), data={"nome": "Cida"}, headers=HX)
    painel = cliente.get(_url(sessao_id, "/llm/painel?pagina=revisao"), headers=HX).text
    assert "Prévia confirmada" not in painel
    assert "Veja a prévia" in painel


def test_confirmar_previa_velha_e_recusado(ativo):
    cliente, sessao_id, _ = ativo
    resposta = cliente.post(_url(sessao_id, "/llm/previa"), data={"impressao": "velha"}, headers=HX)
    assert resposta.status_code == 422
    assert "mudaram" in resposta.text


# --- Gerar ---


def test_gerar_exige_a_previa(ativo, falso):
    cliente, sessao_id, _ = ativo
    resposta = _gerar(cliente, sessao_id)
    assert resposta.status_code == 422
    assert "prévia" in resposta.text
    assert falso.pedidos == []


def test_gerar_com_o_llm_desligado(montar):
    cliente, sessao_id, _ = montar()
    _confirmar_previa(cliente, sessao_id)
    resposta = _gerar(cliente, sessao_id)
    assert resposta.status_code == 422
    assert "desligados" in resposta.text


def test_nunca_durante_a_sessao_ao_vivo(ativo, falso):
    cliente, sessao_id, app = ativo
    _confirmar_previa(cliente, sessao_id)
    with _banco(app) as banco:
        alternar_cronometro(banco, sessao_id)  # cronômetro rodando: sessão ao vivo
    resposta = _gerar(cliente, sessao_id)
    assert resposta.status_code == 422
    assert "ao vivo" in resposta.text
    assert falso.pedidos == []
    painel = cliente.get(_url(sessao_id, "/llm/painel?pagina=revisao"), headers=HX).text
    assert "cronômetro está rodando" in painel


def test_gerar_envia_anonimizado_e_mostra_com_os_nomes(ativo, falso):
    cliente, sessao_id, app = ativo
    _confirmar_previa(cliente, sessao_id)
    resposta = _gerar(cliente, sessao_id)
    assert resposta.status_code == 200
    assert "Hoje o Marcos gasta 60 h por mês; o Roberto quer responder em 1 dia." in resposta.text
    assert "falso-1" in resposta.text
    assert "rascunho_revisao_v1" in resposta.text
    [pedido] = falso.pedidos
    assert "Roberto" not in pedido.mensagem
    assert "Marcos" not in pedido.mensagem
    assert "Anotações do consultor" not in pedido.mensagem
    with _banco(app) as banco:
        [rascunho] = rascunhos_da_sessao(banco, sessao_id)
        assert rascunho.destino is DestinoRascunho.revisao
        assert rascunho.campo == "frase_problema"
        assert rascunho.com_anotacoes_internas is False
        # O texto do consultor não muda sozinho.
        assert textos_da_sessao(banco, sessao_id)["frase_problema"].startswith(
            "Hoje o Marcos gasta"
        )


def test_gerar_com_anotacoes_internas(ativo, falso):
    cliente, sessao_id, app = ativo
    _confirmar_previa(cliente, sessao_id)
    resposta = _gerar(cliente, sessao_id, anotacoes="1")
    assert "usou as anotações internas" in resposta.text
    assert "Anotações do consultor (uso interno)" in falso.pedidos[0].mensagem
    with _banco(app) as banco:
        assert rascunhos_da_sessao(banco, sessao_id)[0].com_anotacoes_internas is True


def test_falha_do_llm_avisa_e_nao_grava(montar):
    cliente, sessao_id, app = montar(
        ProvedorFalso(erro=LLMIndisponivel("Sem conexão com a internet."))
    )
    _confirmar_previa(cliente, sessao_id)
    resposta = _gerar(cliente, sessao_id)
    assert resposta.status_code == 422
    assert "Sem conexão com a internet." in resposta.text
    assert "relatório por template" in resposta.text
    with _banco(app) as banco:
        assert rascunhos_da_sessao(banco, sessao_id) == []


def test_texto_inexistente(ativo):
    cliente, sessao_id, _ = ativo
    _confirmar_previa(cliente, sessao_id)
    assert _gerar(cliente, sessao_id, texto_id="nao_existe").status_code == 404


def test_rascunho_pendente_aparece_na_pagina(ativo):
    cliente, sessao_id, _ = ativo
    _confirmar_previa(cliente, sessao_id)
    _gerar(cliente, sessao_id)
    html = cliente.get(_url(sessao_id, "/revisao")).text
    assert "Hoje o Marcos gasta 60 h por mês; o Roberto quer responder em 1 dia." in html


# --- Aceitar e descartar ---


def _rascunho(app, sessao_id):
    with _banco(app) as banco:
        return rascunhos_da_sessao(banco, sessao_id)[-1]


def test_aceitar_substitui_o_texto(ativo):
    cliente, sessao_id, app = ativo
    _confirmar_previa(cliente, sessao_id)
    _gerar(cliente, sessao_id)
    rascunho = _rascunho(app, sessao_id)
    resposta = cliente.post(_url(sessao_id, f"/rascunhos/{rascunho.id}/aceitar"), headers=HX)
    assert resposta.status_code == 200
    assert resposta.headers["HX-Trigger"] == "revisao-mudou"
    assert 'id="texto-frase_problema"' in resposta.text
    novo = "Hoje o Marcos gasta 60 h por mês; o Roberto quer responder em 1 dia."
    assert f">{novo}</textarea>" in resposta.text
    with _banco(app) as banco:
        assert textos_da_sessao(banco, sessao_id)["frase_problema"] == novo
    assert _rascunho(app, sessao_id).situacao is SituacaoRascunho.aceito


def test_descartar_mantem_o_texto(ativo):
    cliente, sessao_id, app = ativo
    _confirmar_previa(cliente, sessao_id)
    _gerar(cliente, sessao_id)
    rascunho = _rascunho(app, sessao_id)
    resposta = cliente.post(_url(sessao_id, f"/rascunhos/{rascunho.id}/descartar"), headers=HX)
    assert resposta.status_code == 200
    assert "Sugerir rascunho" in resposta.text
    assert _rascunho(app, sessao_id).situacao is SituacaoRascunho.descartado
    with _banco(app) as banco:
        assert textos_da_sessao(banco, sessao_id)["frase_problema"].startswith(
            "Hoje o Marcos gasta"
        )


def test_decidir_duas_vezes(ativo):
    cliente, sessao_id, app = ativo
    _confirmar_previa(cliente, sessao_id)
    _gerar(cliente, sessao_id)
    rascunho = _rascunho(app, sessao_id)
    cliente.post(_url(sessao_id, f"/rascunhos/{rascunho.id}/descartar"), headers=HX)
    resposta = cliente.post(_url(sessao_id, f"/rascunhos/{rascunho.id}/aceitar"), headers=HX)
    assert resposta.status_code == 422
    assert "já foi" in resposta.text


def test_rascunho_de_outra_sessao(ativo):
    cliente, sessao_id, app = ativo
    _confirmar_previa(cliente, sessao_id)
    _gerar(cliente, sessao_id)
    rascunho = _rascunho(app, sessao_id)
    assert cliente.post(_url(sessao_id + 1, f"/rascunhos/{rascunho.id}/aceitar")).status_code == 404
    assert cliente.post(_url(sessao_id, "/rascunhos/999/descartar")).status_code == 404

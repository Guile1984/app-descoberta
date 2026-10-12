"""Rascunhos por LLM na proposta: "Contexto da proposta" e o objetivo de cada fase."""

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from descoberta.demo import popular_demo
from descoberta.llm.falso import ProvedorFalso
from descoberta.repositorio import (
    DestinoRascunho,
    FaseProposta,
    SituacaoRascunho,
    criar_cliente,
    criar_sessao,
    itens_da_sessao,
    rascunhos_da_sessao,
    textos_da_proposta,
)
from descoberta.web.app import criar_app

RAIZ = Path(__file__).resolve().parents[2]
HX = {"HX-Request": "true"}
RESPOSTA = "Para a [EMPRESA], o [PESSOA_1] gasta 60 h por mês nos chamados."
COM_NOMES = "Para a Construtora Alvorada, o Marcos gasta 60 h por mês nos chamados."


@pytest.fixture
def falso():
    return ProvedorFalso(RESPOSTA)


@pytest.fixture
def demo(tmp_path, falso):
    caminho = tmp_path / "demo.db"
    sessao_id = popular_demo(caminho, hoje=date(2026, 10, 11))
    app = criar_app(caminho_banco=caminho, pasta_config=RAIZ / "config", provedor_llm=falso)
    with TestClient(app, follow_redirects=False) as cliente:
        yield cliente, sessao_id, app


def _url(sessao_id, resto=""):
    return f"/sessoes/{sessao_id}{resto}"


def _confirmar_previa(cliente, sessao_id):
    previa = cliente.get(_url(sessao_id, "/llm/previa?pagina=proposta"), headers=HX)
    assert "o texto de contexto que abre a proposta" in previa.text  # pedido da proposta
    impressao = previa.text.split('name="impressao" value="')[1].split('"')[0]
    dados = {"impressao": impressao, "pagina": "proposta"}
    assert cliente.post(_url(sessao_id, "/llm/previa"), data=dados, headers=HX).status_code == 200


def _fases(app, sessao_id):
    with Session(app.state.engine) as banco:
        return itens_da_sessao(banco, FaseProposta, sessao_id)


def test_pagina_tem_o_contexto_e_o_painel(demo):
    cliente, sessao_id, _ = demo
    html = cliente.get(_url(sessao_id, "/proposta")).text
    assert "Contexto da proposta" in html
    assert 'id="proposta-texto-contexto"' in html
    assert "Rascunhos por LLM" in html
    assert 'id="anotacoes-internas"' in html
    assert f'hx-post="/sessoes/{sessao_id}/proposta/textos/contexto/rascunho"' in html
    fase = _fases(demo[2], sessao_id)[0]
    assert f'hx-post="/sessoes/{sessao_id}/proposta/fases/{fase.id}/objetivo/rascunho"' in html


def test_contexto_salva_sozinho_e_vai_para_o_documento(demo):
    cliente, sessao_id, app = demo
    url = _url(sessao_id, "/proposta/textos/contexto")
    resposta = cliente.post(url, data={"texto": "Texto de abertura escrito à mão."}, headers=HX)
    assert resposta.status_code == 200
    assert resposta.headers["HX-Trigger"] == "proposta-mudou"
    with Session(app.state.engine) as banco:
        assert textos_da_proposta(banco, sessao_id) == {
            "contexto": "Texto de abertura escrito à mão."
        }
    documento = cliente.get(_url(sessao_id, "/proposta/documento")).text
    assert "Texto de abertura escrito à mão." in documento
    assert "Esta proposta parte do Relatório de Descoberta" not in documento


def test_texto_de_proposta_desconhecido(demo):
    cliente, sessao_id, _ = demo
    resposta = cliente.post(_url(sessao_id, "/proposta/textos/outro"), data={"texto": "x"})
    assert resposta.status_code == 404


def test_gerar_aceitar_o_contexto(demo, falso):
    cliente, sessao_id, app = demo
    _confirmar_previa(cliente, sessao_id)
    resposta = cliente.post(_url(sessao_id, "/proposta/textos/contexto/rascunho"), headers=HX)
    assert resposta.status_code == 200
    assert COM_NOMES in resposta.text
    [pedido] = falso.pedidos
    assert "o texto de contexto que abre a proposta" in pedido.mensagem
    assert "Construtora Alvorada" not in pedido.mensagem
    assert "Roberto" not in pedido.mensagem
    with Session(app.state.engine) as banco:
        [rascunho] = rascunhos_da_sessao(banco, sessao_id, destino=DestinoRascunho.proposta)
    assert rascunho.campo == "contexto"
    resposta = cliente.post(_url(sessao_id, f"/rascunhos/{rascunho.id}/aceitar"), headers=HX)
    assert resposta.status_code == 200
    assert resposta.headers["HX-Trigger"] == "proposta-mudou"
    assert f">{COM_NOMES}</textarea>" in resposta.text
    with Session(app.state.engine) as banco:
        assert textos_da_proposta(banco, sessao_id) == {"contexto": COM_NOMES}


def test_gerar_aceitar_o_objetivo_da_fase(demo, falso):
    cliente, sessao_id, app = demo
    _confirmar_previa(cliente, sessao_id)
    mvp = _fases(app, sessao_id)[1]
    url = _url(sessao_id, f"/proposta/fases/{mvp.id}/objetivo/rascunho")
    resposta = cliente.post(url, data={"anotacoes": "1"}, headers=HX)
    assert resposta.status_code == 200
    assert 'o objetivo da fase "MVP"' in falso.pedidos[0].mensagem
    assert "Anotações do consultor (uso interno)" in falso.pedidos[0].mensagem
    with Session(app.state.engine) as banco:
        [rascunho] = rascunhos_da_sessao(banco, sessao_id, destino=DestinoRascunho.proposta)
    assert rascunho.campo == f"objetivo_fase.{mvp.id}"
    assert rascunho.com_anotacoes_internas is True
    resposta = cliente.post(_url(sessao_id, f"/rascunhos/{rascunho.id}/aceitar"), headers=HX)
    assert resposta.status_code == 200
    assert resposta.headers["HX-Trigger"] == "proposta-mudou, fases-mudaram"
    assert f'id="fases-{mvp.id}"' in resposta.text
    assert COM_NOMES in resposta.text
    assert _fases(app, sessao_id)[1].objetivo == COM_NOMES


def test_descartar_na_proposta(demo):
    cliente, sessao_id, app = demo
    _confirmar_previa(cliente, sessao_id)
    cliente.post(_url(sessao_id, "/proposta/textos/contexto/rascunho"), headers=HX)
    with Session(app.state.engine) as banco:
        [rascunho] = rascunhos_da_sessao(banco, sessao_id, destino=DestinoRascunho.proposta)
    resposta = cliente.post(_url(sessao_id, f"/rascunhos/{rascunho.id}/descartar"), headers=HX)
    assert 'id="rascunho-proposta-contexto"' in resposta.text
    with Session(app.state.engine) as banco:
        assert rascunhos_da_sessao(banco, sessao_id)[0].situacao is SituacaoRascunho.descartado


def test_fase_de_outra_sessao_ou_inexistente(demo):
    cliente, sessao_id, _ = demo
    _confirmar_previa(cliente, sessao_id)
    url = _url(sessao_id, "/proposta/fases/999/objetivo/rascunho")
    assert cliente.post(url, headers=HX).status_code == 404


def test_sem_proposta(tmp_path, falso):
    caminho = tmp_path / "vazio.db"
    app = criar_app(caminho_banco=caminho, pasta_config=RAIZ / "config", provedor_llm=falso)
    with TestClient(app, follow_redirects=False) as cliente, Session(app.state.engine) as banco:
        cliente_db = criar_cliente(banco, nome="Ana", empresa="Padaria Sol")
        sessao = criar_sessao(
            banco, cliente_id=cliente_db.id, data=date(2026, 10, 9), versao_questionario=1
        )
        url = _url(sessao.id, "/proposta/textos/contexto/rascunho")
        assert cliente.post(url, headers=HX).status_code == 404

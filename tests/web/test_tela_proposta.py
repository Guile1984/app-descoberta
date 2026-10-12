"""Tela da Proposta Comercial: criação (com o aviso do score), edição e documento."""

from pathlib import Path

import pytest

from descoberta.proposta import carregar_modelo_proposta
from descoberta.repositorio import (
    CAMPOS_PROPOSTA,
    FaseProposta,
    ItemProposta,
    TipoItemProposta,
    ajustes_das_clausulas,
    itens_da_sessao,
    obter_proposta,
    salvar_nota,
)
from descoberta.web.proposta import CAMPOS_DAS_CONDICOES, CAMPOS_DO_CLIENTE

HX = {"HX-Request": "true"}


@pytest.fixture
def modelo():
    return carregar_modelo_proposta(
        Path(__file__).resolve().parents[2] / "config" / "proposta_v1.yaml"
    )


def _url(sessao_id: int, resto: str = "") -> str:
    return f"/sessoes/{sessao_id}/proposta{resto}"


def _score_nao_seguir(banco, sessao_id, questionario):
    """Todas as notas zeradas: score final completo, na faixa "não seguir agora"."""
    scores = questionario.scores
    for criterio in scores.prontidao_dados.criterios:
        salvar_nota(banco, sessao_id, criterio.id, 0)
    for criterio in scores.viabilidade_final.criterios:
        if criterio.id != scores.prontidao_dados.criterio_final:
            salvar_nota(banco, sessao_id, criterio.id, 0)


# --- Criação ---


def test_sem_proposta_a_pagina_oferece_criar(cliente_http, sessao):
    html = cliente_http.get(_url(sessao.id)).text
    assert "Criar proposta" in html
    assert f'action="{_url(sessao.id)}"' in html
    assert "advogado" in html  # o aviso do modelo aparece para o consultor


def test_criar_proposta_copia_o_modelo_e_volta_para_a_pagina(cliente_http, banco, sessao):
    resposta = cliente_http.post(_url(sessao.id))
    assert resposta.status_code == 303
    assert resposta.headers["location"] == _url(sessao.id)
    proposta = obter_proposta(banco, sessao.id)
    assert proposta.versao_modelo == 1
    assert proposta.criada_com_alerta is False
    assert len(itens_da_sessao(banco, FaseProposta, sessao.id)) == 2  # score incompleto


def test_score_nao_seguir_avisa_antes_de_criar(cliente_http, banco, sessao, questionario_v1):
    _score_nao_seguir(banco, sessao.id, questionario_v1)
    html = cliente_http.get(_url(sessao.id)).text
    assert "Não seguir agora" in html
    resposta = cliente_http.post(_url(sessao.id))
    assert resposta.status_code == 409
    assert "Criar mesmo assim" in resposta.text
    assert obter_proposta(banco, sessao.id) is None

    resposta = cliente_http.post(_url(sessao.id), data={"confirmar": "1"})
    assert resposta.status_code == 303
    assert obter_proposta(banco, sessao.id).criada_com_alerta is True


def test_score_incompleto_avisa_de_leve(cliente_http, sessao):
    html = cliente_http.get(_url(sessao.id)).text
    assert "score final ainda está incompleto" in html


def test_criar_de_novo_e_recusado(cliente_http, sessao):
    cliente_http.post(_url(sessao.id))
    assert cliente_http.post(_url(sessao.id)).status_code == 409


def test_sessao_inexistente(cliente_http):
    assert cliente_http.get(_url(999)).status_code == 404


# --- Edição ---


@pytest.fixture
def com_proposta(cliente_http, sessao):
    cliente_http.post(_url(sessao.id))
    return sessao


def test_pagina_de_edicao(cliente_http, com_proposta):
    html = cliente_http.get(_url(com_proposta.id)).text
    for titulo in ("Fases", "Escopo por fase", "Entregáveis", "Fora do escopo"):
        assert f">{titulo}</h2>" in html
    for campo, rotulo, _ in CAMPOS_DO_CLIENTE + CAMPOS_DAS_CONDICOES:
        assert f'id="proposta-{campo}"' in html
        assert rotulo in html
    assert "advogado" in html
    assert f'href="{_url(com_proposta.id, "/documento")}"' in html


def test_tela_tem_todos_os_campos_da_proposta():
    na_tela = {campo for campo, _, _ in CAMPOS_DO_CLIENTE + CAMPOS_DAS_CONDICOES}
    assert na_tela == set(CAMPOS_PROPOSTA)


def test_campo_salva_sozinho(cliente_http, banco, com_proposta):
    url = _url(com_proposta.id, "/campo/cliente_cpf_cnpj")
    resposta = cliente_http.post(url, data={"valor": "11222333000181"}, headers=HX)
    assert resposta.status_code == 200
    assert "Salvo" in resposta.text
    assert resposta.headers["HX-Trigger"] == "proposta-mudou"
    banco.expire_all()
    assert obter_proposta(banco, com_proposta.id).cliente_cpf_cnpj == "11.222.333/0001-81"


@pytest.mark.parametrize(
    ("campo", "valor", "erro"),
    [
        ("cliente_cpf_cnpj", "123", "CPF"),
        ("validade_dias", "quinze", "número inteiro"),
        ("validade_dias", "0", "validade"),
        ("reajuste", "", "reajuste"),
    ],
)
def test_campo_invalido(cliente_http, com_proposta, campo, valor, erro):
    url = _url(com_proposta.id, f"/campo/{campo}")
    resposta = cliente_http.post(url, data={"valor": valor}, headers=HX)
    assert resposta.status_code == 422
    assert erro in resposta.text


def test_campo_desconhecido(cliente_http, com_proposta):
    url = _url(com_proposta.id, "/campo/versao_modelo")
    assert cliente_http.post(url, data={"valor": "2"}, headers=HX).status_code == 404


def test_campo_sem_proposta(cliente_http, sessao):
    url = _url(sessao.id, "/campo/reajuste")
    assert cliente_http.post(url, data={"valor": "IPCA"}, headers=HX).status_code == 404


def test_incluir_item_de_fase(cliente_http, banco, com_proposta):
    fase = itens_da_sessao(banco, FaseProposta, com_proposta.id)[1]
    dados = {"texto": "Painel de acompanhamento", "fase_id": str(fase.id)}
    resposta = cliente_http.post(_url(com_proposta.id, "/escopo"), data=dados, headers=HX)
    assert resposta.status_code == 200
    assert "Painel de acompanhamento" in resposta.text
    escopo = itens_da_sessao(banco, ItemProposta, com_proposta.id, tipo=TipoItemProposta.escopo)
    assert escopo[-1].fase_id == fase.id


def test_item_de_fase_exige_a_fase(cliente_http, com_proposta):
    resposta = cliente_http.post(
        _url(com_proposta.id, "/entregaveis"), data={"texto": "X"}, headers=HX
    )
    assert resposta.status_code == 422
    assert "escolha a fase" in resposta.text


def test_mudar_fases_recarrega_o_escopo(cliente_http, com_proposta):
    dados = {"nome": "Sustentação", "duracao_semanas": "4", "investimento": "1.500"}
    resposta = cliente_http.post(_url(com_proposta.id, "/fases"), data=dados, headers=HX)
    assert resposta.headers["HX-Trigger"] == "proposta-mudou, fases-mudaram"
    assert "R$ 1.500,00" in resposta.text
    escopo = cliente_http.get(_url(com_proposta.id, "/escopo"), headers=HX).text
    assert 'hx-trigger="fases-mudaram from:body"' in escopo
    assert ">Sustentação</option>" in escopo


def test_fase_com_numero_invalido(cliente_http, com_proposta):
    dados = {"nome": "X", "duracao_semanas": "duas"}
    resposta = cliente_http.post(_url(com_proposta.id, "/fases"), data=dados, headers=HX)
    assert resposta.status_code == 422
    assert "número inteiro" in resposta.text


def test_editar_fase_mostra_o_valor_como_se_digita(cliente_http, banco, com_proposta):
    fase = itens_da_sessao(banco, FaseProposta, com_proposta.id)[0]
    url = _url(com_proposta.id, f"/fases/{fase.id}")
    cliente_http.post(url, data={"nome": fase.nome, "investimento": "6.000"}, headers=HX)
    html = cliente_http.get(url + "/editar", headers=HX).text
    assert 'value="6.000"' in html


def test_item_de_outra_lista_nao_e_encontrado(cliente_http, banco, com_proposta):
    premissa = itens_da_sessao(
        banco, ItemProposta, com_proposta.id, tipo=TipoItemProposta.premissa
    )[0]
    assert cliente_http.get(_url(com_proposta.id, f"/exclusoes/{premissa.id}")).status_code == 404


def test_recriar_apaga_e_volta_ao_inicio(cliente_http, banco, com_proposta):
    resposta = cliente_http.post(_url(com_proposta.id, "/recriar"), headers=HX)
    assert resposta.headers["HX-Redirect"] == _url(com_proposta.id)
    assert obter_proposta(banco, com_proposta.id) is None


# --- Documento ---


def test_documento_da_proposta_do_roberto(cliente_demo):
    cliente, sessao_id = cliente_demo
    html = cliente.get(_url(sessao_id, "/documento")).text
    assert "1. Identificação das partes" in html
    assert "R$ 26.000,00" in html
    assert "advogado" in html  # aviso para o consultor, fora do documento
    for formato in ("pdf", "docx", "md"):
        assert f'href="{_url(sessao_id, "." + formato)}"' in html


@pytest.mark.parametrize(
    ("formato", "tipo"),
    [
        ("pdf", "application/pdf"),
        ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("md", "text/markdown; charset=utf-8"),
    ],
)
def test_baixar_rascunho(cliente_demo, formato, tipo):
    cliente, sessao_id = cliente_demo
    resposta = cliente.get(_url(sessao_id, f".{formato}"))
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == tipo
    assert resposta.headers["content-disposition"] == (
        f'attachment; filename="proposta-comercial-construtora-alvorada-2026-10-07.{formato}"'
    )


def test_documento_sem_proposta(cliente_http, sessao):
    assert cliente_http.get(_url(sessao.id, "/documento")).status_code == 404
    assert cliente_http.get(_url(sessao.id, ".pdf")).status_code == 404


def test_formato_desconhecido(cliente_demo):
    cliente, sessao_id = cliente_demo
    assert cliente.get(_url(sessao_id, ".odt")).status_code == 404


def test_links_para_a_proposta(cliente_demo):
    cliente, sessao_id = cliente_demo
    for pagina in ("/revisao", "/relatorio"):
        html = cliente.get(f"/sessoes/{sessao_id}{pagina}").text
        assert f'href="{_url(sessao_id)}"' in html


# --- Condições Gerais ---


def _clausula(sessao_id, clausula_id, resto=""):
    return _url(sessao_id, f"/clausulas/{clausula_id}{resto}")


def test_condicoes_gerais_na_edicao(cliente_http, com_proposta):
    html = cliente_http.get(_url(com_proposta.id)).text
    assert ">Condições Gerais</h2>" in html
    assert 'id="clausula-foro"' in html
    assert "{foro}" in html  # o texto mostra o marcador; o documento mostra a cidade
    assert "Não removível" in html


def test_ajustar_texto_salva_sozinho(cliente_http, banco, com_proposta):
    url = _clausula(com_proposta.id, "suporte_garantia")
    resposta = cliente_http.post(url, data={"texto": "Garantia de 90 dias."}, headers=HX)
    assert resposta.status_code == 200
    assert resposta.headers["HX-Trigger"] == "proposta-mudou"
    assert ajustes_das_clausulas(banco, com_proposta.id)["suporte_garantia"].texto == (
        "Garantia de 90 dias."
    )


def test_voltar_ao_texto_do_modelo_desfaz_o_ajuste(cliente_http, banco, com_proposta, modelo):
    url = _clausula(com_proposta.id, "foro")
    cliente_http.post(url, data={"texto": "Outro."}, headers=HX)
    cliente_http.post(url, data={"texto": modelo.clausula("foro").texto + "  "}, headers=HX)
    banco.expire_all()
    assert ajustes_das_clausulas(banco, com_proposta.id) == {}


@pytest.mark.parametrize(
    ("texto", "erro"), [("", "Excluir"), ("Foro de {cidade}.", "marcador desconhecido")]
)
def test_ajuste_invalido(cliente_http, com_proposta, texto, erro):
    url = _clausula(com_proposta.id, "foro")
    resposta = cliente_http.post(url, data={"texto": texto}, headers=HX)
    assert resposta.status_code == 422
    assert erro in resposta.text


def test_clausula_inexistente(cliente_http, com_proposta):
    url = _clausula(com_proposta.id, "xyz")
    assert cliente_http.post(url, data={"texto": "X"}, headers=HX).status_code == 404


def test_excluir_e_incluir_de_volta(cliente_http, banco, com_proposta):
    url = _clausula(com_proposta.id, "cancelamento", "/excluir")
    resposta = cliente_http.post(url, data={"excluir": "1"}, headers=HX)
    assert resposta.status_code == 200
    assert "Fora desta proposta" in resposta.text
    assert "Incluir de volta" in resposta.text
    assert ajustes_das_clausulas(banco, com_proposta.id)["cancelamento"].excluida is True
    resposta = cliente_http.post(url, data={"excluir": "0"}, headers=HX)
    banco.expire_all()
    assert ajustes_das_clausulas(banco, com_proposta.id)["cancelamento"].excluida is False


def test_nao_removivel_nao_e_excluida(cliente_http, banco, com_proposta):
    url = _clausula(com_proposta.id, "lgpd", "/excluir")
    resposta = cliente_http.post(url, data={"excluir": "1"}, headers=HX)
    assert resposta.status_code == 422
    assert "não pode ser excluída" in resposta.text
    assert ajustes_das_clausulas(banco, com_proposta.id) == {}


def test_restaurar(cliente_http, banco, com_proposta, modelo):
    url = _clausula(com_proposta.id, "suporte_garantia")
    cliente_http.post(url, data={"texto": "Outro."}, headers=HX)
    resposta = cliente_http.post(url + "/restaurar", headers=HX)
    assert modelo.clausula("suporte_garantia").texto in resposta.text
    banco.expire_all()
    assert ajustes_das_clausulas(banco, com_proposta.id) == {}

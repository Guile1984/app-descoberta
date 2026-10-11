"""Área de revisão pós-sessão: textos do relatório, listas, matriz de riscos e pendências."""

import re
from datetime import date

import pytest

from descoberta.repositorio import (
    Indicador,
    ItemEscopo,
    ProximoPasso,
    Risco,
    adicionar_item,
    criar_sessao,
    itens_da_sessao,
    salvar_resposta,
    salvar_texto_secao,
    textos_da_sessao,
)

HX = {"HX-Request": "true"}

RISCO = {
    "descricao": "Fotos mostram o interior das casas",
    "categoria": "lgpd",
    "probabilidade": "alto",
    "impacto": "alto",
    "mitigacao": "Recortar a área da fissura",
}


def _itens(banco, modelo, sessao_id):
    banco.expire_all()
    return itens_da_sessao(banco, modelo, sessao_id)


def _celula(html: str, impacto: str, probabilidade: str) -> str:
    """O conteúdo da célula da matriz (impacto × probabilidade)."""
    achado = re.search(
        rf'<td[^>]*data-impacto="{impacto}" data-probabilidade="{probabilidade}"[^>]*>(.*?)</td>',
        html,
        re.S,
    )
    assert achado, f"célula {impacto} × {probabilidade} não encontrada"
    return achado.group(1)


# --- Página ---


def test_tela_ao_vivo_tem_link_para_a_revisao(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert f'href="/sessoes/{sessao.id}/revisao"' in html


def test_pagina_da_revisao(cliente_http, sessao, questionario_v1):
    resposta = cliente_http.get(f"/sessoes/{sessao.id}/revisao")
    assert resposta.status_code == 200
    html = resposta.text
    assert "Revisão pós-sessão" in html
    assert f'href="/sessoes/{sessao.id}"' in html  # volta para a tela ao vivo
    for texto in questionario_v1.revisao.textos:
        assert texto.titulo in html
        assert f'id="texto-{texto.id}"' in html
    for secao in ("lista-riscos", "lista-indicadores", "lista-escopo", "lista-passos"):
        assert f'id="{secao}"' in html
    assert 'id="matriz-riscos"' in html
    assert 'id="pendencias-revisao"' in html


def test_sessao_inexistente_da_404(cliente_http):
    assert cliente_http.get("/sessoes/999/revisao").status_code == 404


def test_categorias_vem_do_yaml(cliente_http, sessao, questionario_v1):
    html = cliente_http.get(f"/sessoes/{sessao.id}/revisao").text
    for categoria in questionario_v1.revisao.categorias_risco:
        assert f'<option value="{categoria.id}"' in html
        assert categoria.rotulo in html


def test_textos_de_apoio_mostram_o_que_foi_dito_na_sessao(cliente_http, banco, sessao):
    salvar_resposta(banco, sessao.id, "enc.recomendacao", "Seguir com fase 0 <logo>")
    html = cliente_http.get(f"/sessoes/{sessao.id}/revisao").text
    assert "Seguir com fase 0 &lt;logo&gt;" in html
    assert "Recomendação preliminar" in html  # título do item do encerramento
    assert "sem resposta" in html  # apoio de outros textos ainda em branco


# --- Textos das seções ---


def test_texto_salva_e_avisa_a_revisao(cliente_http, banco, sessao):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/textos/frase_problema",
        data={"texto": "Hoje o Marcos gasta 60 h/mês…"},
        headers=HX,
    )
    assert resposta.status_code == 200
    assert "Salvo às" in resposta.text
    assert resposta.headers["HX-Trigger"] == "revisao-mudou"
    banco.expire_all()
    assert textos_da_sessao(banco, sessao.id) == {"frase_problema": "Hoje o Marcos gasta 60 h/mês…"}


def test_texto_gravado_aparece_na_caixa(cliente_http, banco, sessao):
    salvar_texto_secao(banco, sessao.id, "recomendacao", "Seguir & ver")
    html = cliente_http.get(f"/sessoes/{sessao.id}/revisao").text
    assert "Seguir &amp; ver</textarea>" in html


def test_secao_inexistente_da_404(cliente_http, sessao):
    resposta = cliente_http.post(f"/sessoes/{sessao.id}/textos/conclusao", data={"texto": "x"})
    assert resposta.status_code == 404


# --- Riscos e matriz ---


def test_adicionar_risco_devolve_a_lista_e_avisa(cliente_http, banco, sessao):
    resposta = cliente_http.post(f"/sessoes/{sessao.id}/revisao/riscos", data=RISCO, headers=HX)
    assert resposta.status_code == 200
    assert "<html" not in resposta.text
    assert 'id="lista-riscos"' in resposta.text
    assert "Fotos mostram o interior das casas" in resposta.text
    assert "R1" in resposta.text
    assert resposta.headers["HX-Trigger"] == "revisao-mudou"
    [risco] = _itens(banco, Risco, sessao.id)
    assert (risco.categoria, risco.probabilidade, risco.impacto) == ("lgpd", "alto", "alto")


def test_risco_com_categoria_fora_do_yaml_e_recusado(cliente_http, banco, sessao):
    dados = RISCO | {"categoria": "espionagem"}
    resposta = cliente_http.post(f"/sessoes/{sessao.id}/revisao/riscos", data=dados, headers=HX)
    assert resposta.status_code == 422
    assert "Não salvo" in resposta.text
    assert "espionagem" in resposta.text
    assert "Fotos mostram o interior das casas" in resposta.text  # o texto digitado não some
    assert _itens(banco, Risco, sessao.id) == []


def test_risco_sem_descricao_e_recusado(cliente_http, banco, sessao):
    dados = RISCO | {"descricao": " "}
    resposta = cliente_http.post(f"/sessoes/{sessao.id}/revisao/riscos", data=dados, headers=HX)
    assert resposta.status_code == 422
    assert "Recortar a área da fissura" in resposta.text
    assert "HX-Trigger" not in resposta.headers


def test_matriz_mostra_o_risco_na_celula_certa(cliente_http, banco, sessao):
    adicionar_item(banco, Risco, sessao.id, **RISCO)
    adicionar_item(
        banco,
        Risco,
        sessao.id,
        **(RISCO | {"descricao": "API cara", "impacto": "medio", "probabilidade": "baixo"}),
    )
    html = cliente_http.get(f"/sessoes/{sessao.id}/revisao/matriz", headers=HX).text
    assert "<html" not in html
    assert "R1" in _celula(html, "alto", "alto")
    assert "R2" in _celula(html, "medio", "baixo")
    assert "tag-risco" not in _celula(html, "baixo", "alto")


def test_matriz_e_pendencias_se_atualizam_com_o_evento(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}/revisao").text
    assert html.count('hx-trigger="revisao-mudou from:body"') == 2


def test_editar_risco(cliente_http, banco, sessao):
    risco = adicionar_item(banco, Risco, sessao.id, **RISCO)
    url = f"/sessoes/{sessao.id}/revisao/riscos/{risco.id}"
    formulario = cliente_http.get(f"{url}/editar", headers=HX).text
    assert "<textarea" in formulario or "<input" in formulario
    assert 'value="alto" selected' in formulario
    assert "Fotos mostram o interior das casas" in formulario

    resposta = cliente_http.post(url, data=RISCO | {"impacto": "baixo"}, headers=HX)
    assert resposta.status_code == 200
    assert 'id="lista-riscos"' in resposta.text
    assert resposta.headers["HX-Trigger"] == "revisao-mudou"
    assert _itens(banco, Risco, sessao.id)[0].impacto == "baixo"


def test_cancelar_edicao(cliente_http, banco, sessao):
    risco = adicionar_item(banco, Risco, sessao.id, **RISCO)
    html = cliente_http.get(f"/sessoes/{sessao.id}/revisao/riscos/{risco.id}", headers=HX).text
    assert "Fotos mostram o interior das casas" in html
    assert "<select" not in html


def test_edicao_invalida_volta_so_o_item_com_o_erro(cliente_http, banco, sessao):
    risco = adicionar_item(banco, Risco, sessao.id, **RISCO)
    url = f"/sessoes/{sessao.id}/revisao/riscos/{risco.id}"
    resposta = cliente_http.post(url, data=RISCO | {"probabilidade": "enorme"}, headers=HX)
    assert resposta.status_code == 422
    assert "Não salvo" in resposta.text
    # O formulário de edição mira a lista inteira; com erro, a resposta vai só para o item.
    assert resposta.headers["HX-Retarget"] == f"#riscos-{risco.id}"
    assert resposta.headers["HX-Reswap"] == "outerHTML"
    assert _itens(banco, Risco, sessao.id)[0].probabilidade == "alto"


def test_excluir_risco(cliente_http, banco, sessao):
    risco = adicionar_item(banco, Risco, sessao.id, **RISCO)
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/revisao/riscos/{risco.id}/excluir", headers=HX
    )
    assert resposta.status_code == 200
    assert 'id="lista-riscos"' in resposta.text
    assert resposta.headers["HX-Trigger"] == "revisao-mudou"
    assert _itens(banco, Risco, sessao.id) == []


def test_item_de_outra_sessao_da_404(cliente_http, banco, sessao, cliente):
    outra = criar_sessao(
        banco, cliente_id=cliente.id, data=date(2026, 10, 8), versao_questionario=1
    )
    risco = adicionar_item(banco, Risco, outra.id, **RISCO)
    url = f"/sessoes/{sessao.id}/revisao/riscos/{risco.id}"
    assert cliente_http.get(url).status_code == 404
    assert cliente_http.post(f"{url}/excluir").status_code == 404
    assert len(_itens(banco, Risco, outra.id)) == 1


def test_lista_inexistente_da_404(cliente_http, sessao):
    assert cliente_http.post(f"/sessoes/{sessao.id}/revisao/orcamento", data={}).status_code == 404


def test_html_dos_itens_e_escapado(cliente_http, sessao):
    dados = RISCO | {"descricao": "<script>alert(1)</script>"}
    html = cliente_http.post(f"/sessoes/{sessao.id}/revisao/riscos", data=dados, headers=HX).text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


# --- Indicadores, escopo e próximos passos ---


def test_adicionar_indicador(cliente_http, banco, sessao):
    dados = {
        "nome": "Horas do Marcos com chamados",
        "camada": "negocio",
        "valor_atual": "60 h/mês",
        "meta": "30 h/mês",
        "prazo": "3 meses após a entrega",
        "como_medir": "Planilha de chamados",
    }
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/revisao/indicadores", data=dados, headers=HX
    )
    assert resposta.status_code == 200
    assert "Negócio" in resposta.text
    [indicador] = _itens(banco, Indicador, sessao.id)
    assert (indicador.valor_atual, indicador.meta) == ("60 h/mês", "30 h/mês")


def test_adicionar_itens_de_escopo(cliente_http, banco, sessao):
    url = f"/sessoes/{sessao.id}/revisao/escopo"
    cliente_http.post(url, data={"texto": "Triagem por foto", "entra": "sim"})
    html = cliente_http.post(url, data={"texto": "Laudo automático", "entra": "nao"}).text
    assert html.index("Triagem por foto") < html.index("Laudo automático")
    itens = _itens(banco, ItemEscopo, sessao.id)
    assert [(i.texto, i.entra) for i in itens] == [
        ("Triagem por foto", True),
        ("Laudo automático", False),
    ]


def test_escopo_com_valor_estranho_e_recusado(cliente_http, banco, sessao):
    url = f"/sessoes/{sessao.id}/revisao/escopo"
    resposta = cliente_http.post(url, data={"texto": "Triagem", "entra": "talvez"}, headers=HX)
    assert resposta.status_code == 422
    assert _itens(banco, ItemEscopo, sessao.id) == []


def test_adicionar_proximo_passo_com_data(cliente_http, banco, sessao):
    dados = {"acao": "Enviar os 40 casos graves", "responsavel": "cliente", "prazo": "2026-10-14"}
    html = cliente_http.post(f"/sessoes/{sessao.id}/revisao/passos", data=dados, headers=HX).text
    assert "14/10/2026" in html
    assert "Cliente" in html
    [passo] = _itens(banco, ProximoPasso, sessao.id)
    assert passo.prazo == date(2026, 10, 14)


def test_proximo_passo_sem_prazo(cliente_http, banco, sessao):
    dados = {"acao": "Validar critério", "responsavel": "consultor", "prazo": ""}
    cliente_http.post(f"/sessoes/{sessao.id}/revisao/passos", data=dados)
    assert _itens(banco, ProximoPasso, sessao.id)[0].prazo is None


@pytest.mark.parametrize("prazo", ["14/10/2026", "amanhã"])
def test_prazo_fora_do_formato_do_navegador_e_recusado(cliente_http, banco, sessao, prazo):
    dados = {"acao": "Validar critério", "responsavel": "consultor", "prazo": prazo}
    resposta = cliente_http.post(f"/sessoes/{sessao.id}/revisao/passos", data=dados, headers=HX)
    assert resposta.status_code == 422
    assert _itens(banco, ProximoPasso, sessao.id) == []


# --- Pendências ---


def test_pendencias_da_revisao_vazia(cliente_http, sessao, questionario_v1):
    html = cliente_http.get(f"/sessoes/{sessao.id}/revisao/pendencias", headers=HX).text
    assert "<html" not in html
    assert "nenhum risco cadastrado" in html
    assert "nenhum indicador de negócio" in html
    assert "nenhum próximo passo" in html
    assert questionario_v1.texto_revisao("resumo_executivo").titulo in html
    # As obrigatórias da sessão ao vivo também contam.
    assert "obrigatórias sem resposta" in html


def test_pendencia_some_quando_o_dado_chega(cliente_http, banco, sessao):
    adicionar_item(banco, Risco, sessao.id, **(RISCO | {"mitigacao": ""}))
    html = cliente_http.get(f"/sessoes/{sessao.id}/revisao/pendencias", headers=HX).text
    assert "nenhum risco cadastrado" not in html
    assert "exigem mitigação" in html


def test_revisao_do_roberto_sem_pendencias(cliente_demo):
    cliente, sessao_id = cliente_demo
    html = cliente.get(f"/sessoes/{sessao_id}/revisao").text
    assert "Nada falta" in html
    assert "R1" in html


def test_risco_sem_categoria_pede_para_escolher(cliente_http, sessao):
    dados = RISCO | {"categoria": ""}
    resposta = cliente_http.post(f"/sessoes/{sessao.id}/revisao/riscos", data=dados, headers=HX)
    assert resposta.status_code == 422
    assert "escolha a categoria" in resposta.text


def test_formularios_de_edicao_mostram_data_sim_ou_nao_e_campos_vazios(cliente_http, banco, sessao):
    passo = adicionar_item(
        banco,
        ProximoPasso,
        sessao.id,
        acao="Amostra",
        responsavel="cliente",
        prazo=date(2026, 10, 14),
    )
    item = adicionar_item(banco, ItemEscopo, sessao.id, texto="Laudo automático", entra=False)
    indicador = adicionar_item(banco, Indicador, sessao.id, nome="Horas", camada="negocio")
    base = f"/sessoes/{sessao.id}/revisao"

    html = cliente_http.get(f"{base}/passos/{passo.id}/editar", headers=HX).text
    assert 'value="2026-10-14"' in html  # formato do <input type="date">
    html = cliente_http.get(f"{base}/escopo/{item.id}/editar", headers=HX).text
    assert 'value="nao" selected' in html
    html = cliente_http.get(f"{base}/indicadores/{indicador.id}/editar", headers=HX).text
    assert f'id="indicadores-{indicador.id}-meta" name="meta" value=""' in html

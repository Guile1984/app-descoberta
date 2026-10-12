"""Sessão ao vivo: troca de aba, obrigatórias pendentes, encerramento e atalhos."""

import json
import re
from pathlib import Path

from descoberta.demo import ANOTACOES
from descoberta.repositorio import atualizar_sessao, respostas_da_sessao, salvar_resposta
from descoberta.web.atalhos import ATALHOS

HX = {"HX-Request": "true"}
ATALHOS_JS = Path(__file__).resolve().parents[2] / "src/descoberta/web/static/atalhos.js"


# --- Troca de aba ---


def test_troca_de_aba_traz_os_sinais_e_o_bloco_da_anotacao_fora_do_painel(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=3", headers=HX).text
    # hx-swap-oob: o HTMX encaixa esses pedaços nos elementos de mesmo id da coluna direita,
    # sem redesenhar a coluna (uma anotação sendo digitada não se perde).
    assert re.search(r'id="sinais"[^>]*hx-swap-oob="true"', html)
    assert re.search(r'id="anotacao-bloco"[^>]*hx-swap-oob="true"', html)
    assert "b3.s1" in html
    assert 'id="anotacao-texto"' not in html  # o formulário da anotação fica onde está


def test_pagina_inteira_nao_usa_troca_fora_do_painel(cliente_http, sessao):
    assert "hx-swap-oob" not in cliente_http.get(f"/sessoes/{sessao.id}?bloco=3").text


# --- Obrigatórias pendentes ---


def test_total_de_pendentes_no_topo(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert 'id="pendencias"' in html
    assert "48 obrigatórias pendentes" in html


def test_cada_aba_mostra_quantas_obrigatorias_faltam(cliente_http, banco, sessao):
    salvar_resposta(banco, sessao.id, "b1.o1", "Fissuras")
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert 'data-aba="1" data-pendentes="6"' in html
    assert 'data-aba="2" data-pendentes="5"' in html


def test_condicionais_entram_nas_pendentes_quando_aparecem(cliente_http, banco, sessao):
    atualizar_sessao(banco, sessao.id, tipo_solucao="visao_computacional")
    html = cliente_http.get(f"/sessoes/{sessao.id}/pendencias", headers=HX).text
    assert "52 obrigatórias pendentes" in html


def test_salvar_resposta_avisa_as_pendencias(cliente_http, sessao):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/respostas/b1.o1", data={"texto": "Fissuras"}, headers=HX
    )
    assert resposta.headers["HX-Trigger"] == "pendencias-mudaram"


def test_trocar_o_tipo_de_solucao_avisa_as_pendencias(cliente_http, sessao):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/campos/tipo_solucao",
        data={"valor": "visao_computacional"},
        headers=HX,
    )
    assert resposta.headers["HX-Trigger"] == "pendencias-mudaram"


def test_abas_e_pendencias_se_atualizam_sozinhas(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=2").text
    assert f'hx-get="/sessoes/{sessao.id}/abas?atual=2"' in html
    assert f'hx-get="/sessoes/{sessao.id}/pendencias"' in html
    assert html.count("pendencias-mudaram from:body") >= 2


def test_campos_obrigatorios_marcados_para_o_atalho_de_pendentes(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=1", headers=HX).text
    assert re.search(r'<textarea[^>]*id="resposta-b1-o1"[^>]*data-obrigatoria', html)
    assert not re.search(r'<textarea[^>]*id="resposta-b1-a1"[^>]*data-obrigatoria', html)


# --- Encerramento ---


def test_aba_de_encerramento(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert f'href="/sessoes/{sessao.id}/encerramento"' in html
    pagina = cliente_http.get(f"/sessoes/{sessao.id}/encerramento").text
    assert "<html" in pagina
    for titulo in ("Resumo", "Recomendação preliminar", "Próximos passos", "Prazo"):
        assert titulo in pagina
    assert f'hx-post="/sessoes/{sessao.id}/respostas/enc.resumo"' in pagina


def test_encerramento_pelo_htmx_vem_so_o_painel(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}/encerramento", headers=HX).text
    assert "<html" not in html
    assert re.search(r'id="sinais"[^>]*hx-swap-oob="true"', html)


def test_respostas_do_encerramento_sao_salvas(cliente_http, banco, sessao):
    resposta = cliente_http.post(
        f"/sessoes/{sessao.id}/respostas/enc.prazo", data={"texto": "Até sexta."}, headers=HX
    )
    assert resposta.status_code == 200
    assert respostas_da_sessao(banco, sessao.id) == {"enc.prazo": "Até sexta."}


def test_resumo_para_ler_ao_cliente(cliente_http, banco, sessao):
    salvar_resposta(banco, sessao.id, "enc.resumo", "Os chamados de fissura tomam 60 h/mês.")
    html = cliente_http.get(f"/sessoes/{sessao.id}/encerramento/resumo", headers=HX).text
    assert "Os chamados de fissura tomam 60 h/mês." in html
    assert "a preencher" in html  # itens ainda em branco
    assert "48 obrigatórias pendentes" in html


def test_resumo_traz_a_recomendacao_do_painel(cliente_demo):
    cliente, sessao_id = cliente_demo
    html = cliente.get(f"/sessoes/{sessao_id}/encerramento/resumo", headers=HX).text
    assert "Seguir com fase 0" in html
    assert "12 de 18" in html
    assert "7,7 meses" in html


def test_banco_de_demonstracao_mostra_numeros_notas_e_sinais(cliente_demo):
    # Pendência do Sprint 4: o banco de demonstração já tem métricas, notas e sinais.
    cliente, sessao_id = cliente_demo
    bloco_1 = cliente.get(f"/sessoes/{sessao_id}?bloco=1").text
    assert 'value="4"' in bloco_1  # horas por ocorrência
    assert 'aria-pressed="true"' in bloco_1  # b1.s4 marcado
    for texto, _bloco in ANOTACOES:
        assert texto in bloco_1
    bloco_4 = cliente.get(f"/sessoes/{sessao_id}?bloco=4", headers=HX).text
    assert re.search(r'<option value="0" selected', bloco_4)  # qualidade = 0


# --- Atalhos ---


def test_ajuda_lista_todos_os_atalhos(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert '<dialog id="ajuda-atalhos"' in html
    for atalho in ATALHOS:
        assert atalho.descricao in html
        assert atalho.teclas in html


def test_lista_de_atalhos_vai_para_o_js_como_json(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    dados = re.search(r'<script type="application/json" id="atalhos-dados">(.*?)</script>', html)
    lista = json.loads(dados.group(1))
    assert [item["acao"] for item in lista] == [atalho.acao for atalho in ATALHOS]
    assert 'src="/static/atalhos.js"' in html


def test_toda_acao_tem_tratamento_no_js():
    codigo = ATALHOS_JS.read_text(encoding="utf-8")
    for atalho in ATALHOS:
        assert re.search(rf"^\s+{atalho.acao}\(", codigo, re.MULTILINE), atalho.acao


def test_ajuda_abre_com_ctrl_barra_e_interrogacao():
    [ajuda] = [atalho for atalho in ATALHOS if atalho.acao == "ajuda"]
    combinacoes = [c.para_js() for c in ajuda.combinacoes]
    assert {"key": "/", "ctrl": True} in combinacoes
    assert {"key": "?", "fora_de_campo": True} in combinacoes


def test_alt_mais_numero_vai_para_os_10_blocos():
    [bloco] = [atalho for atalho in ATALHOS if atalho.acao == "bloco"]
    assert [(c.code, c.argumento) for c in bloco.combinacoes] == [
        *((f"Digit{n}", n) for n in range(1, 10)),
        ("Digit0", 10),
    ]


def test_atalhos_nao_usam_teclas_do_navegador():
    # Alt+D (endereço), Alt+E e Alt+F (menu) do Chrome e do Edge.
    usadas = {c.code for atalho in ATALHOS for c in atalho.combinacoes if c.alt}
    assert not usadas & {"KeyD", "KeyE", "KeyF"}


def test_sem_combinacoes_repetidas():
    vistas = [(c.code, c.key, c.alt, c.ctrl) for atalho in ATALHOS for c in atalho.combinacoes]
    assert len(vistas) == len(set(vistas))


def test_botao_de_ajuda_visivel_na_sessao(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert 'data-acao="ajuda"' in html
    assert "Ctrl+/" in html


def test_paginas_fora_da_sessao_nao_carregam_os_atalhos(cliente_http, perfil):
    assert "atalhos.js" not in cliente_http.get("/").text

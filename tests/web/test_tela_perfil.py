"""Tela do perfil do consultor e o pedido de preenchimento no primeiro uso."""

import io

from PIL import Image

from descoberta.repositorio import obter_perfil, salvar_logotipo, salvar_perfil

DADOS = {
    "nome": "Ana Exemplo",
    "empresa": "Exemplo Consultoria em IA Ltda",
    "cpf_cnpj": "11.222.333/0001-81",
    "email": "ana@example.com",
    "telefone": "(11) 90000-0000",
    "cidade": "São Paulo",
    "uf": "SP",
}


def _png(cor="navy") -> bytes:
    saida = io.BytesIO()
    Image.new("RGB", (60, 30), cor).save(saida, "PNG")
    return saida.getvalue()


def test_primeiro_uso_a_tela_inicial_leva_ao_perfil(cliente_http):
    resposta = cliente_http.get("/")
    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/perfil?primeiro_uso=1"


def test_com_perfil_a_tela_inicial_abre(cliente_http, banco):
    salvar_perfil(banco, nome="Ana", empresa="Exemplo")
    assert cliente_http.get("/").status_code == 200


def test_outras_paginas_nao_redirecionam(cliente_http, sessao):
    assert cliente_http.get(f"/sessoes/{sessao.id}").status_code == 200
    assert cliente_http.get("/clientes/novo").status_code == 200


def test_formulario_do_primeiro_uso(cliente_http):
    html = cliente_http.get("/perfil?primeiro_uso=1").text
    assert "Antes de começar" in html
    assert 'name="primeiro_uso" value="1"' in html
    assert 'enctype="multipart/form-data"' in html
    assert "fica só neste computador" in html


def test_salvar_no_primeiro_uso_volta_para_a_tela_inicial(cliente_http, banco):
    resposta = cliente_http.post("/perfil", data={**DADOS, "primeiro_uso": "1"})
    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/"
    perfil = obter_perfil(banco)
    assert perfil.cpf_cnpj == "11.222.333/0001-81"
    assert perfil.uf == "SP"


def test_salvar_depois_fica_no_perfil_com_aviso(cliente_http):
    resposta = cliente_http.post("/perfil", data=DADOS)
    assert resposta.headers["location"] == "/perfil?salvo=1"
    assert "Perfil salvo" in cliente_http.get("/perfil?salvo=1").text


def test_formulario_mostra_os_dados_gravados(cliente_http, banco):
    salvar_perfil(banco, **DADOS)
    html = cliente_http.get("/perfil").text
    assert 'value="Ana Exemplo"' in html
    assert 'value="11.222.333/0001-81"' in html
    assert '<option value="SP" selected>' in html


def test_erro_volta_ao_formulario_com_o_que_foi_digitado(cliente_http, banco):
    resposta = cliente_http.post("/perfil", data={**DADOS, "cpf_cnpj": "111.444.777-36"})
    assert resposta.status_code == 422
    assert "dígito verificador" in resposta.text
    assert 'value="Ana Exemplo"' in resposta.text
    assert obter_perfil(banco) is None


def test_enviar_logotipo(cliente_http, banco):
    arquivos = {"logotipo": ("logo.png", _png(), "image/png")}
    resposta = cliente_http.post("/perfil", data=DADOS, files=arquivos)
    assert resposta.status_code == 303
    assert obter_perfil(banco).logotipo.startswith(b"\x89PNG")
    imagem = cliente_http.get("/perfil/logotipo.png")
    assert imagem.headers["content-type"] == "image/png"
    assert imagem.content == obter_perfil(banco).logotipo
    assert '<img src="/perfil/logotipo.png' in cliente_http.get("/perfil").text


def test_logotipo_invalido_nao_grava_nada(cliente_http, banco):
    arquivos = {"logotipo": ("logo.gif", b"GIF89a...", "image/gif")}
    resposta = cliente_http.post("/perfil", data=DADOS, files=arquivos)
    assert resposta.status_code == 422
    assert "PNG ou JPEG" in resposta.text
    assert obter_perfil(banco) is None  # nem os outros campos


def test_sem_arquivo_mantem_o_logotipo(cliente_http, banco):
    salvar_perfil(banco, **DADOS)
    salvar_logotipo(banco, _png())
    vazio = {"logotipo": ("", b"", "application/octet-stream")}
    cliente_http.post("/perfil", data={**DADOS, "telefone": "123"}, files=vazio)
    banco.expire_all()
    assert obter_perfil(banco).logotipo is not None


def test_remover_logotipo(cliente_http, banco):
    salvar_perfil(banco, **DADOS)
    salvar_logotipo(banco, _png())
    cliente_http.post("/perfil", data={**DADOS, "remover_logotipo": "1"})
    banco.expire_all()
    assert obter_perfil(banco).logotipo is None
    assert cliente_http.get("/perfil/logotipo.png").status_code == 404


def test_menu_tem_o_perfil(cliente_http, banco):
    salvar_perfil(banco, nome="Ana", empresa="Exemplo")
    assert 'href="/perfil"' in cliente_http.get("/").text

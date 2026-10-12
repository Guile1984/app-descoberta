"""Telas de cliente: lista, cadastro, edição e exclusão."""

from descoberta.repositorio import listar_clientes, listar_sessoes, obter_cliente

HX = {"HX-Request": "true"}


def test_lista_vazia_convida_a_cadastrar(cliente_http, perfil):
    resposta = cliente_http.get("/")
    assert resposta.status_code == 200
    assert "Nenhum cliente cadastrado" in resposta.text


def test_cadastro_valido_redireciona_para_o_cliente(cliente_http, banco, perfil):
    resposta = cliente_http.post(
        "/clientes",
        data={
            "nome": "Roberto",
            "empresa": "Construtora Alvorada",
            "setor": "Construção civil",
            "num_funcionarios": "35",
            "contato": "",
        },
    )
    assert resposta.status_code == 303
    [cliente] = listar_clientes(banco)
    assert resposta.headers["location"] == f"/clientes/{cliente.id}"
    assert cliente.num_funcionarios == 35
    assert cliente.contato is None  # campo em branco vira "sem valor"
    assert "Construtora Alvorada" in cliente_http.get("/").text


def test_cadastro_sem_nome_volta_com_a_mensagem(cliente_http, banco):
    resposta = cliente_http.post("/clientes", data={"nome": " ", "empresa": "Alvorada"})
    assert resposta.status_code == 422
    assert "nome não pode ficar vazio" in resposta.text
    assert 'value="Alvorada"' in resposta.text  # o que foi digitado não se perde
    assert listar_clientes(banco) == []


def test_numero_de_funcionarios_invalido(cliente_http, banco):
    resposta = cliente_http.post(
        "/clientes", data={"nome": "Roberto", "empresa": "Alvorada", "num_funcionarios": "abc"}
    )
    assert resposta.status_code == 422
    assert "número inteiro" in resposta.text
    assert listar_clientes(banco) == []


def test_edicao(cliente_http, banco, cliente):
    assert cliente_http.get(f"/clientes/{cliente.id}/editar").status_code == 200
    resposta = cliente_http.post(
        f"/clientes/{cliente.id}",
        data={"nome": "Roberto", "empresa": "Construtora Alvorada Ltda", "setor": "Obras"},
    )
    assert resposta.status_code == 303
    banco.expire_all()
    assert obter_cliente(banco, cliente.id).empresa == "Construtora Alvorada Ltda"


def test_pagina_do_cliente_lista_as_sessoes(cliente_http, sessao, cliente):
    resposta = cliente_http.get(f"/clientes/{cliente.id}")
    assert resposta.status_code == 200
    assert f'href="/sessoes/{sessao.id}"' in resposta.text
    assert "07/10/2026" in resposta.text


def test_cliente_inexistente_da_404(cliente_http):
    assert cliente_http.get("/clientes/999").status_code == 404


def test_exclusao_apaga_as_sessoes_e_redireciona(cliente_http, banco, cliente, sessao):
    cliente_id = cliente.id  # depois de excluir, o objeto não vale mais
    resposta = cliente_http.post(f"/clientes/{cliente_id}/excluir", headers=HX)
    # Num pedido do HTMX, o redirecionamento vem no cabeçalho HX-Redirect.
    assert resposta.headers["HX-Redirect"] == "/"
    banco.expire_all()
    assert obter_cliente(banco, cliente_id) is None
    assert listar_sessoes(banco, cliente_id) == []


def test_botao_de_exclusao_pede_confirmacao(cliente_http, cliente):
    assert "hx-confirm=" in cliente_http.get(f"/clientes/{cliente.id}").text


def test_edicao_invalida_nao_grava(cliente_http, banco, cliente):
    resposta = cliente_http.post(f"/clientes/{cliente.id}", data={"nome": "", "empresa": "X"})
    assert resposta.status_code == 422
    assert "nome não pode ficar vazio" in resposta.text
    banco.expire_all()
    assert obter_cliente(banco, cliente.id).empresa == "Construtora Alvorada"

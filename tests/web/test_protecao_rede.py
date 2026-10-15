"""A app só atende o próprio computador.

Duas proteções para quem usa a app no notebook enquanto navega em outros sites:
- Host: só 127.0.0.1 e localhost. Barra o "DNS rebinding", em que um site malicioso faz o
  navegador achar que o endereço dele é 127.0.0.1 e lê as páginas da app.
- Origem: pedidos que gravam (POST, PUT, PATCH, DELETE) só valem vindos da própria app.
  Barra um site malicioso que envia um formulário escondido para 127.0.0.1:8000 (CSRF).
"""

import pytest

URL_GRAVACAO = "/perfil"
NOME = "Consultora Zuleica Teste"
DADOS_PERFIL = {"nome": NOME, "empresa": "Empresa Teste"}


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "127.0.0.1:8000", "localhost:8123"])
def test_aceita_o_proprio_computador(cliente_http, host):
    assert cliente_http.get("/", headers={"host": host}).status_code in (200, 303)


@pytest.mark.parametrize("host", ["atacante.example", "192.168.0.10:8000", "0.0.0.0"])
def test_recusa_outros_hosts(cliente_http, host):
    resposta = cliente_http.get("/", headers={"host": host})
    assert resposta.status_code == 400


def test_static_tambem_e_protegido(cliente_http):
    resposta = cliente_http.get("/static/htmx.min.js", headers={"host": "atacante.example"})
    assert resposta.status_code == 400


@pytest.mark.parametrize(
    "cabecalhos",
    [
        {"origin": "https://atacante.example"},
        {"origin": "null"},  # páginas em sandbox ou arquivos locais mandam "null"
        {"origin": "http://127.0.0.1:9999"},  # outra app local, em outra porta
        {"sec-fetch-site": "cross-site"},
        {"sec-fetch-site": "same-site"},
    ],
    ids=["outro-site", "origem-nula", "outra-porta", "cross-site", "same-site"],
)
def test_recusa_gravacao_vinda_de_fora(cliente_http, cabecalhos):
    resposta = cliente_http.post(URL_GRAVACAO, data=DADOS_PERFIL, headers=cabecalhos)
    assert resposta.status_code == 403
    assert cliente_http.get("/perfil").status_code == 200  # nada foi gravado...
    assert NOME not in cliente_http.get("/perfil").text


@pytest.mark.parametrize(
    "cabecalhos",
    [
        {"origin": "http://127.0.0.1", "sec-fetch-site": "same-origin"},
        {"sec-fetch-site": "same-origin"},
        {"sec-fetch-site": "none"},  # endereço digitado ou favorito
        {},  # navegadores antigos e ferramentas não mandam nenhum dos dois
    ],
    ids=["mesma-origem", "so-sec-fetch", "digitado", "sem-cabecalhos"],
)
def test_aceita_gravacao_da_propria_app(cliente_http, cabecalhos):
    resposta = cliente_http.post(URL_GRAVACAO, data=DADOS_PERFIL, headers=cabecalhos)
    assert resposta.status_code in (200, 303)
    assert NOME in cliente_http.get("/perfil").text


def test_leitura_vinda_de_outro_site_continua_permitida(cliente_http):
    # Um link para a app num e-mail ou documento é normal; só gravar é que fica barrado.
    resposta = cliente_http.get("/", headers={"sec-fetch-site": "cross-site"})
    assert resposta.status_code in (200, 303)

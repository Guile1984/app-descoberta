"""Perguntas condicionais na tela (pendência do Sprint 3).

Quando o tipo de solução muda, as condicionais que deixam de valer somem da tela, mas as
respostas continuam no banco; se o tipo voltar, elas reaparecem preenchidas.
"""

from descoberta.repositorio import respostas_da_sessao

HX = {"HX-Request": "true"}
RESPOSTA_VC1 = "Os mestres de obra e os clientes, pelo celular."


def _escolher_tipo(cliente_http, sessao_id, tipo):
    resposta = cliente_http.post(
        f"/sessoes/{sessao_id}/campos/tipo_solucao", data={"valor": tipo}, headers=HX
    )
    assert resposta.status_code == 200


def _bloco_4(cliente_http, sessao_id) -> str:
    return cliente_http.get(f"/sessoes/{sessao_id}?bloco=4", headers=HX).text


def test_ida_e_volta_do_tipo_de_solucao(cliente_http, banco, sessao):
    assert "b4.vc1" not in _bloco_4(cliente_http, sessao.id)

    _escolher_tipo(cliente_http, sessao.id, "visao_computacional")
    html = _bloco_4(cliente_http, sessao.id)
    for id_ in ("b4.vc1", "b4.vc2", "b4.vc3", "b4.vc4"):
        assert id_ in html
    cliente_http.post(
        f"/sessoes/{sessao.id}/respostas/b4.vc1", data={"texto": RESPOSTA_VC1}, headers=HX
    )

    _escolher_tipo(cliente_http, sessao.id, "llm_rag")
    html = _bloco_4(cliente_http, sessao.id)
    assert "b4.vc1" not in html
    assert RESPOSTA_VC1 not in html
    assert respostas_da_sessao(banco, sessao.id) == {"b4.vc1": RESPOSTA_VC1}  # não apagou

    _escolher_tipo(cliente_http, sessao.id, "visao_computacional")
    assert RESPOSTA_VC1 in _bloco_4(cliente_http, sessao.id)


def test_tipo_em_aberto_esconde_as_condicionais(cliente_http, sessao):
    _escolher_tipo(cliente_http, sessao.id, "visao_computacional")
    _escolher_tipo(cliente_http, sessao.id, "")
    assert "b4.vc1" not in _bloco_4(cliente_http, sessao.id)

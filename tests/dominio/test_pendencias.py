"""Obrigatórias ainda sem resposta, por bloco (respeitando as condicionais)."""

from descoberta.dominio.pendencias import obrigatorias_pendentes


def test_sessao_nova_tem_todas_as_obrigatorias_visiveis_pendentes(questionario_v1):
    pendentes = obrigatorias_pendentes(questionario_v1, None, [])
    assert list(pendentes) == list(range(1, 11))
    assert sum(len(ids) for ids in pendentes.values()) == 48
    assert "b4.vc1" not in pendentes[4]  # condicional escondida não conta


def test_condicionais_visiveis_contam_como_pendentes(questionario_v1):
    pendentes = obrigatorias_pendentes(questionario_v1, "visao_computacional", [])
    assert {"b4.vc1", "b4.vc2", "b4.vc3", "b4.vc4"} <= set(pendentes[4])


def test_respondidas_e_aprofundamento_nao_contam(questionario_v1):
    pendentes = obrigatorias_pendentes(questionario_v1, None, ["b1.o1", "b1.o2", "b1.a1"])
    assert "b1.o1" not in pendentes[1]
    assert "b1.o3" in pendentes[1]
    assert not any(id_.startswith("b1.a") for id_ in pendentes[1])


def test_resposta_de_condicional_escondida_e_ignorada(questionario_v1):
    pendentes = obrigatorias_pendentes(questionario_v1, None, ["b4.vc1"])
    assert sum(len(ids) for ids in pendentes.values()) == 48

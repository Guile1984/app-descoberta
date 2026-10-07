"""Contagem dos sinais de alerta marcados, por bloco."""

import pytest

from descoberta.dominio.sinais import contar_sinais_por_bloco


def test_sem_sinais_marcados_todos_os_blocos_tem_zero(questionario_v1):
    assert contar_sinais_por_bloco(questionario_v1, []) == dict.fromkeys(range(1, 11), 0)


def test_conta_por_bloco(questionario_v1):
    contagem = contar_sinais_por_bloco(questionario_v1, ["b1.s1", "b1.s3", "b4.s2", "b9.s4"])
    assert contagem[1] == 2
    assert contagem[4] == 1
    assert contagem[9] == 1
    assert sum(contagem.values()) == 4


def test_todos_os_blocos_aparecem_mesmo_sem_sinais_no_catalogo(questionario_v1):
    # O bloco 10 (relatório) não tem sinais de alerta, mas aparece com 0.
    assert contar_sinais_por_bloco(questionario_v1, ["b1.s1"])[10] == 0


def test_sinal_repetido_conta_uma_vez(questionario_v1):
    assert contar_sinais_por_bloco(questionario_v1, ["b2.s1", "b2.s1"])[2] == 1


def test_todos_marcados(questionario_v1):
    todos = [sinal.id for bloco in questionario_v1.blocos for sinal in bloco.sinais]
    contagem = contar_sinais_por_bloco(questionario_v1, todos)
    assert contagem == {bloco.numero: len(bloco.sinais) for bloco in questionario_v1.blocos}


def test_id_desconhecido_gera_erro(questionario_v1):
    with pytest.raises(ValueError, match="'b4.s99'"):
        contar_sinais_por_bloco(questionario_v1, ["b1.s1", "b4.s99"])

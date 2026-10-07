"""Caso de referência "Construtora Alvorada / Roberto", de ponta a ponta.

Parte das entradas brutas da sessão (fixture `caso_roberto`, em tests/conftest.py, onde
estão as hipóteses registradas), usa as faixas do questionário v1 real e chega à
recomendação final. Valores de referência (CLAUDE.md e especificação): 60 h/mês de dor,
score de dados 4, payback ≈ 7,7 meses, score final 12 → seguir com fase 0.
"""

from decimal import Decimal

from descoberta.dominio.dor import custo_dor_mes, horas_dor_mes, ocorrencias_por_mes
from descoberta.dominio.operacao import custo_operacao_mes
from descoberta.dominio.payback import economia_mes, payback_dificil_de_aprovar, payback_meses
from descoberta.dominio.scores import (
    nota_prontidao_para_viabilidade,
    score_prontidao,
    score_viabilidade,
)
from descoberta.dominio.sinais import contar_sinais_por_bloco


def test_caso_roberto_de_ponta_a_ponta(questionario_v1, caso_roberto):
    caso = caso_roberto

    # Bloco 1 — custo da dor: 15 ocorrências por mês × 4 h por ocorrência.
    ocorrencias = ocorrencias_por_mes(caso.frequencia_quantidade, caso.frequencia_periodo)
    horas = horas_dor_mes(caso.horas_por_ocorrencia, ocorrencias)
    assert horas == 60
    assert custo_dor_mes(horas, caso.custo_hora) == Decimal(6000)

    # Bloco 4 — prontidão de dados.
    dados = score_prontidao(caso.notas_dados, questionario_v1)
    assert dados.pontuacao == 4
    assert dados.faixa.id == "fase_0"
    nota_dados = nota_prontidao_para_viabilidade(dados.pontuacao, questionario_v1)
    assert nota_dados == 1

    # Blocos 1, 6 e 9 — economia, operação e payback.
    economia = economia_mes(caso.horas_economizadas_mes, caso.custo_hora)
    operacao = custo_operacao_mes(custo_fixo_mes=caso.custo_fixo_mes)
    assert economia == 3000
    assert operacao == 400
    meses = payback_meses(caso.investimento, economia, operacao)
    assert round(meses, 1) == Decimal("7.7")  # 20.000 / 2.600 = 7,69…
    assert not payback_dificil_de_aprovar(meses)

    # Bloco 10 — score final de viabilidade.
    final = score_viabilidade(
        caso.notas_viabilidade | {"prontidao_dados": nota_dados}, questionario_v1
    )
    assert final.pontuacao == 12
    assert final.faixa.id == "seguir_fase_0"
    assert final.faixa.rotulo == "Seguir com fase 0"


def test_caso_roberto_sinais_de_alerta(questionario_v1, caso_roberto):
    textos = {sinal.id: sinal.texto for bloco in questionario_v1.blocos for sinal in bloco.sinais}
    for id_, trecho in caso_roberto.sinais_marcados.items():
        assert trecho in textos[id_], f"o texto do sinal {id_} mudou no YAML"

    contagem = contar_sinais_por_bloco(questionario_v1, caso_roberto.sinais_marcados)
    assert contagem == dict.fromkeys(range(1, 11), 0) | {1: 1, 2: 2, 8: 1, 9: 1}

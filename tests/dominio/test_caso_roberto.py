"""Caso de referência "Construtora Alvorada / Roberto", de ponta a ponta.

Parte das entradas brutas da sessão, usa as faixas do questionário v1 real e chega à
recomendação final. Valores de referência (CLAUDE.md e especificação): 60 h/mês de dor,
score de dados 4, payback ≈ 7,7 meses, score final 12 → seguir com fase 0.

Hipóteses registradas (não ditas pelo cliente, assumidas pelo consultor):
- custo da hora: R$ 100 (Modelo de Descoberta: "30 horas economizadas por mês valem R$ 3.000");
- a solução economiza 30 das 60 horas mensais;
- a operação de R$ 400/mês é custo fixo (sem cobrança por chamada).
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

CUSTO_HORA = 100  # hipótese
HORAS_ECONOMIZADAS_MES = 30  # hipótese
INVESTIMENTO = 20_000
CUSTO_FIXO_OPERACAO = 400

NOTAS_DADOS = {
    "disponibilidade": 1,
    "volume": 1,
    "rotulos": 1,
    "qualidade": 0,
    "acesso_legal": 1,
}

# Sinais de alerta marcados na sessão: id → trecho do texto no YAML.
SINAIS_MARCADOS = {
    "b1.s4": "100% de acerto ou zero intervenção humana",
    "b2.s2": "concentrado em uma pessoa que não participa",
    "b2.s3": "informação que não é registrada",
    "b8.s4": "ninguém para manter a solução",
    "b9.s1": "Orçamento indefinido",
}


def test_caso_roberto_de_ponta_a_ponta(questionario_v1):
    # Bloco 1 — custo da dor: 15 ocorrências por mês × 4 h por ocorrência.
    horas = horas_dor_mes(horas_por_ocorrencia=4, ocorrencias_mes=ocorrencias_por_mes(15, "mes"))
    assert horas == 60
    assert custo_dor_mes(horas, CUSTO_HORA) == Decimal(6000)

    # Bloco 4 — prontidão de dados.
    dados = score_prontidao(NOTAS_DADOS, questionario_v1)
    assert dados.pontuacao == 4
    assert dados.faixa.id == "fase_0"
    nota_dados = nota_prontidao_para_viabilidade(dados.pontuacao, questionario_v1)
    assert nota_dados == 1

    # Blocos 1, 6 e 9 — economia, operação e payback.
    economia = economia_mes(HORAS_ECONOMIZADAS_MES, CUSTO_HORA)
    operacao = custo_operacao_mes(custo_fixo_mes=CUSTO_FIXO_OPERACAO)
    assert economia == 3000
    assert operacao == 400
    meses = payback_meses(INVESTIMENTO, economia, operacao)
    assert round(meses, 1) == Decimal("7.7")  # 20.000 / 2.600 = 7,69…
    assert not payback_dificil_de_aprovar(meses)

    # Bloco 10 — score final de viabilidade.
    final = score_viabilidade(
        {
            "dor_clara": 3,
            "ia_caminho_certo": 2,
            "prontidao_dados": nota_dados,
            "retorno_viavel": 2,
            "riscos_controlaveis": 2,
            "comprometimento_cliente": 2,
        },
        questionario_v1,
    )
    assert final.pontuacao == 12
    assert final.faixa.id == "seguir_fase_0"
    assert final.faixa.rotulo == "Seguir com fase 0"


def test_caso_roberto_sinais_de_alerta(questionario_v1):
    textos = {sinal.id: sinal.texto for bloco in questionario_v1.blocos for sinal in bloco.sinais}
    for id_, trecho in SINAIS_MARCADOS.items():
        assert trecho in textos[id_], f"o texto do sinal {id_} mudou no YAML"

    contagem = contar_sinais_por_bloco(questionario_v1, SINAIS_MARCADOS)
    assert contagem == dict.fromkeys(range(1, 11), 0) | {1: 1, 2: 2, 8: 1, 9: 1}

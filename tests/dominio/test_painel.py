"""Painel de cálculos ao vivo: junta os cálculos do domínio com os dados que já existem."""

from dataclasses import fields
from decimal import Decimal

import pytest

from descoberta.dominio.painel import EntradasPainel, calcular_painel


def entradas_do_caso(caso) -> EntradasPainel:
    return EntradasPainel(
        horas_por_ocorrencia=caso.horas_por_ocorrencia,
        frequencia_quantidade=caso.frequencia_quantidade,
        frequencia_periodo=caso.frequencia_periodo,
        custo_hora=caso.custo_hora,
        horas_economizadas_mes=caso.horas_economizadas_mes,
        investimento=caso.investimento,
        custo_fixo_mes=caso.custo_fixo_mes,
    )


def test_caso_roberto_no_painel(questionario_v1, caso_roberto):
    painel = calcular_painel(
        entradas_do_caso(caso_roberto),
        caso_roberto.notas_dados | caso_roberto.notas_viabilidade,
        caso_roberto.sinais_marcados,
        questionario_v1,
    )
    assert painel.ocorrencias_mes.valor == 15
    assert painel.horas_dor_mes.valor == 60
    assert painel.custo_dor_mes.valor == 6000
    assert painel.operacao_mes.valor == 400
    assert painel.economia_mes.valor == 3000
    assert round(painel.payback.meses, 1) == Decimal("7.7")
    assert painel.payback.nunca_se_paga is False
    assert painel.payback.dificil_de_aprovar is False
    assert painel.score_dados.pontuacao == 4
    assert painel.score_dados.resultado.faixa.id == "fase_0"
    assert painel.nota_prontidao == 1
    assert painel.score_final.pontuacao == 12
    assert painel.score_final.faltando == ()
    assert painel.score_final.resultado.faixa.rotulo == "Seguir com fase 0"
    assert painel.sinais_por_bloco == dict.fromkeys(range(1, 11), 0) | {1: 1, 2: 2, 8: 1, 9: 1}


def test_painel_vazio_diz_o_que_falta_em_cada_calculo(questionario_v1):
    painel = calcular_painel(EntradasPainel(), {}, [], questionario_v1)
    assert painel.ocorrencias_mes.valor is None
    assert painel.ocorrencias_mes.faltando == ("frequencia_quantidade", "frequencia_periodo")
    assert painel.horas_dor_mes.faltando == (
        "horas_por_ocorrencia",
        "frequencia_quantidade",
        "frequencia_periodo",
    )
    assert painel.custo_dor_mes.faltando == (
        "horas_por_ocorrencia",
        "frequencia_quantidade",
        "frequencia_periodo",
        "custo_hora",
    )
    assert painel.operacao_mes.faltando == (
        "chamadas_por_dia",
        "custo_por_chamada",
        "custo_fixo_mes",
    )
    assert painel.economia_mes.faltando == ("horas_economizadas_mes", "custo_hora")
    assert painel.payback.meses is None
    assert painel.payback.nunca_se_paga is False
    assert painel.payback.dificil_de_aprovar is None
    assert "investimento" in painel.payback.faltando
    assert painel.score_dados.resultado is None
    assert painel.nota_prontidao is None
    assert "prontidao_dados" in painel.score_final.faltando
    assert set(painel.sinais_por_bloco.values()) == {0}


def test_faltando_nao_repete_o_mesmo_campo(questionario_v1):
    painel = calcular_painel(EntradasPainel(), {}, [], questionario_v1)
    for calculo in (painel.custo_dor_mes, painel.payback):
        assert len(calculo.faltando) == len(set(calculo.faltando))


def test_custo_da_dor_com_frequencia_semanal(questionario_v1):
    entradas = EntradasPainel(
        horas_por_ocorrencia=2, frequencia_quantidade=3, frequencia_periodo="semana", custo_hora=50
    )
    painel = calcular_painel(entradas, {}, [], questionario_v1)
    assert painel.ocorrencias_mes.valor == 13  # 3 × 52 / 12
    assert painel.horas_dor_mes.valor == 26
    assert painel.custo_dor_mes.valor == 1300


@pytest.mark.parametrize(
    ("campos", "valor", "faltando"),
    [
        ({"custo_fixo_mes": 400}, Decimal(400), ()),
        ({"chamadas_por_dia": 10, "custo_por_chamada": Decimal("0.5")}, Decimal(110), ()),
        (
            {"chamadas_por_dia": 10, "custo_por_chamada": 1, "custo_fixo_mes": 100},
            Decimal(320),
            (),
        ),
        ({"chamadas_por_dia": 10}, None, ("custo_por_chamada",)),
        ({"custo_por_chamada": 1, "custo_fixo_mes": 100}, None, ("chamadas_por_dia",)),
    ],
)
def test_custo_de_operacao(questionario_v1, campos, valor, faltando):
    painel = calcular_painel(EntradasPainel(**campos), {}, [], questionario_v1)
    assert painel.operacao_mes.valor == valor
    assert painel.operacao_mes.faltando == faltando


def test_outros_ganhos_entram_na_economia(questionario_v1):
    entradas = EntradasPainel(horas_economizadas_mes=10, custo_hora=100, outros_ganhos_mes=500)
    assert calcular_painel(entradas, {}, [], questionario_v1).economia_mes.valor == 1500


def test_projeto_que_nunca_se_paga(questionario_v1):
    entradas = EntradasPainel(
        horas_economizadas_mes=1, custo_hora=100, investimento=1000, custo_fixo_mes=400
    )
    payback = calcular_painel(entradas, {}, [], questionario_v1).payback
    assert payback.meses is None
    assert payback.faltando == ()
    assert payback.nunca_se_paga is True
    assert payback.dificil_de_aprovar is True


def test_payback_acima_de_12_meses_e_dificil_de_aprovar(questionario_v1):
    entradas = EntradasPainel(
        horas_economizadas_mes=10, custo_hora=100, investimento=26_000, custo_fixo_mes=0
    )
    payback = calcular_painel(entradas, {}, [], questionario_v1).payback
    assert payback.meses == 26
    assert payback.dificil_de_aprovar is True


def test_score_final_parcial_usa_a_nota_derivada_dos_dados(questionario_v1, caso_roberto):
    painel = calcular_painel(EntradasPainel(), caso_roberto.notas_dados, [], questionario_v1)
    assert painel.nota_prontidao == 1
    assert painel.score_final.pontuacao == 1
    assert "prontidao_dados" not in painel.score_final.faltando
    assert len(painel.score_final.faltando) == 5


def test_score_de_dados_incompleto_nao_gera_nota_derivada(questionario_v1):
    painel = calcular_painel(EntradasPainel(), {"volume": 3, "dor_clara": 2}, [], questionario_v1)
    assert painel.score_dados.pontuacao == 3
    assert painel.nota_prontidao is None
    assert painel.score_final.pontuacao == 2
    assert "prontidao_dados" in painel.score_final.faltando


def test_nota_dada_a_mao_para_o_criterio_derivado_e_recusada(questionario_v1):
    with pytest.raises(ValueError, match="prontidao_dados"):
        calcular_painel(EntradasPainel(), {"prontidao_dados": 2}, [], questionario_v1)


def test_nota_de_criterio_desconhecido_e_recusada(questionario_v1):
    with pytest.raises(ValueError, match="prazo"):
        calcular_painel(EntradasPainel(), {"prazo": 2}, [], questionario_v1)


def test_entradas_tem_os_nomes_dos_parametros_das_metricas():
    # A web passa as métricas gravadas direto para o painel: os nomes precisam ser os
    # mesmos campos (o teste da web confere o outro lado, contra a tabela Metricas).
    assert [campo.name for campo in fields(EntradasPainel)] == [
        "horas_por_ocorrencia",
        "frequencia_quantidade",
        "frequencia_periodo",
        "custo_hora",
        "horas_economizadas_mes",
        "outros_ganhos_mes",
        "investimento",
        "chamadas_por_dia",
        "custo_por_chamada",
        "custo_fixo_mes",
    ]


def test_cada_calculo_diz_de_quais_entradas_depende(questionario_v1):
    # Usado pela memória de cálculo do relatório para marcar "depende de hipótese".
    for painel in (
        calcular_painel(EntradasPainel(), {}, [], questionario_v1),
        calcular_painel(
            EntradasPainel(custo_hora=100, horas_economizadas_mes=30), {}, [], questionario_v1
        ),
    ):
        assert painel.ocorrencias_mes.entradas == ("frequencia_quantidade", "frequencia_periodo")
        assert painel.horas_dor_mes.entradas == (
            "horas_por_ocorrencia",
            "frequencia_quantidade",
            "frequencia_periodo",
        )
        assert painel.custo_dor_mes.entradas == (
            "horas_por_ocorrencia",
            "frequencia_quantidade",
            "frequencia_periodo",
            "custo_hora",
        )
        assert painel.operacao_mes.entradas == (
            "chamadas_por_dia",
            "custo_por_chamada",
            "custo_fixo_mes",
        )
        assert painel.economia_mes.entradas == (
            "horas_economizadas_mes",
            "custo_hora",
            "outros_ganhos_mes",
        )
        assert painel.payback.entradas == (
            "investimento",
            "horas_economizadas_mes",
            "custo_hora",
            "outros_ganhos_mes",
            "chamadas_por_dia",
            "custo_por_chamada",
            "custo_fixo_mes",
        )


class _Registro:
    """Qualquer objeto com os atributos certos (ex.: a tabela Metricas)."""

    horas_por_ocorrencia = 4
    custo_hora = 100
    outro_campo = "ignorado"


def test_entradas_a_partir_de_um_registro():
    entradas = EntradasPainel.de(_Registro())
    assert entradas.horas_por_ocorrencia == 4
    assert entradas.custo_hora == 100
    assert entradas.investimento is None


def test_entradas_de_nada_ficam_vazias():
    assert EntradasPainel.de(None) == EntradasPainel()

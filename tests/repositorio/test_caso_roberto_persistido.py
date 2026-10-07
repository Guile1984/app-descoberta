"""Caso Roberto gravado no banco, relido do zero e recalculado com o domínio.

Garante que nada se perde no caminho (Decimal, ids do YAML, notas) e que o que sai do
banco serve direto para os cálculos do Sprint 2.
"""

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from descoberta.dominio.dor import horas_dor_mes, ocorrencias_por_mes
from descoberta.dominio.operacao import custo_operacao_mes
from descoberta.dominio.payback import economia_mes, payback_meses
from descoberta.dominio.scores import (
    nota_prontidao_para_viabilidade,
    score_prontidao,
    score_viabilidade,
)
from descoberta.dominio.sinais import contar_sinais_por_bloco
from descoberta.repositorio import (
    criar_cliente,
    criar_sessao,
    marcar_sinal,
    notas_da_sessao,
    obter_metricas,
    obter_sessao,
    salvar_metricas,
    salvar_nota,
    sinais_marcados,
)


def _gravar(engine, caso) -> int:
    with Session(engine) as session:
        cliente = criar_cliente(session, nome="Roberto", empresa="Construtora Alvorada")
        sessao = criar_sessao(
            session,
            cliente_id=cliente.id,
            data=date(2026, 10, 7),
            versao_questionario=1,
            tipo_solucao="ml_classico",
        )
        salvar_metricas(
            session,
            sessao.id,
            horas_por_ocorrencia=caso.horas_por_ocorrencia,
            frequencia_quantidade=caso.frequencia_quantidade,
            frequencia_periodo=caso.frequencia_periodo,
            custo_hora=caso.custo_hora,
            horas_economizadas_mes=caso.horas_economizadas_mes,
            investimento=caso.investimento,
            custo_fixo_mes=caso.custo_fixo_mes,
        )
        for criterio, nota in (caso.notas_dados | caso.notas_viabilidade).items():
            salvar_nota(session, sessao.id, criterio, nota)
        for sinal_id in caso.sinais_marcados:
            marcar_sinal(session, sessao.id, sinal_id)
        return sessao.id


def test_caso_roberto_sobrevive_ao_banco(engine, questionario_v1, caso_roberto):
    sessao_id = _gravar(engine, caso_roberto)

    # Sessão nova: nada vem da memória, tudo é lido do arquivo.
    with Session(engine) as session:
        sessao = obter_sessao(session, sessao_id)
        assert sessao.versao_questionario == questionario_v1.versao
        m = obter_metricas(session, sessao_id)
        notas = notas_da_sessao(session, sessao_id)
        sinais = [s.sinal_id for s in sinais_marcados(session, sessao_id)]

    horas = horas_dor_mes(
        m.horas_por_ocorrencia,
        ocorrencias_por_mes(m.frequencia_quantidade, m.frequencia_periodo),
    )
    assert horas == 60

    # As notas dos dois scores ficam na mesma tabela; cada score pega os seus critérios,
    # conforme o questionário.
    criterios_dados = {c.id for c in questionario_v1.scores.prontidao_dados.criterios}
    criterios_final = {c.id for c in questionario_v1.scores.viabilidade_final.criterios}
    dados = score_prontidao(
        {c: n for c, n in notas.items() if c in criterios_dados}, questionario_v1
    )
    assert dados.pontuacao == 4

    economia = economia_mes(m.horas_economizadas_mes, m.custo_hora, m.outros_ganhos_mes or 0)
    operacao = custo_operacao_mes(custo_fixo_mes=m.custo_fixo_mes)
    meses = payback_meses(m.investimento, economia, operacao)
    assert round(meses, 1) == Decimal("7.7")

    nota_dados = nota_prontidao_para_viabilidade(dados.pontuacao, questionario_v1)
    final = score_viabilidade(
        {c: n for c, n in notas.items() if c in criterios_final} | {"prontidao_dados": nota_dados},
        questionario_v1,
    )
    assert final.pontuacao == 12
    assert final.faixa.rotulo == "Seguir com fase 0"

    assert contar_sinais_por_bloco(questionario_v1, sinais) == dict.fromkeys(range(1, 11), 0) | {
        1: 1,
        2: 2,
        8: 1,
        9: 1,
    }

"""Métricas e notas dos scores na tela, e o painel de cálculos ao vivo."""

from dataclasses import fields
from decimal import Decimal
from typing import get_args

import pytest

from descoberta.dominio.dor import Periodo
from descoberta.dominio.painel import EntradasPainel
from descoberta.repositorio import (
    Metricas,
    marcar_sinal,
    notas_da_sessao,
    obter_metricas,
    salvar_metricas,
    salvar_nota,
)
from descoberta.web.campos import CAMPOS_METRICAS, PERIODOS

HX = {"HX-Request": "true"}


def _metrica(cliente_http, sessao_id, campo, valor):
    return cliente_http.post(
        f"/sessoes/{sessao_id}/metricas/{campo}", data={"valor": valor}, headers=HX
    )


def _nota(cliente_http, sessao_id, criterio, valor):
    return cliente_http.post(
        f"/sessoes/{sessao_id}/notas/{criterio}", data={"valor": valor}, headers=HX
    )


# --- Campos das métricas ---


def test_campos_da_tela_cobrem_todas_as_metricas_do_banco():
    nomes = [campo.nome for campo in CAMPOS_METRICAS]
    assert set(nomes) == set(Metricas.model_fields) - {"sessao_id"}
    assert set(nomes) == {campo.name for campo in fields(EntradasPainel)}
    assert set(PERIODOS) == set(get_args(Periodo))


@pytest.mark.parametrize(
    ("bloco", "campos"),
    [
        (1, ["horas_por_ocorrencia", "frequencia_quantidade", "custo_hora"]),
        (6, ["chamadas_por_dia", "custo_por_chamada", "custo_fixo_mes"]),
        (9, ["horas_economizadas_mes", "outros_ganhos_mes", "investimento"]),
    ],
)
def test_cada_bloco_mostra_os_seus_campos_numericos(cliente_http, sessao, bloco, campos):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco={bloco}", headers=HX).text
    for campo in campos:
        assert f'hx-post="/sessoes/{sessao.id}/metricas/{campo}"' in html


def test_bloco_sem_metricas_nao_mostra_campos(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=2", headers=HX).text
    assert "/metricas/" not in html


def test_metrica_em_formato_brasileiro_e_salva_e_avisa_os_calculos(cliente_http, banco, sessao):
    resposta = _metrica(cliente_http, sessao.id, "investimento", "20.000")
    assert resposta.status_code == 200
    assert "Salvo às" in resposta.text
    assert resposta.headers["HX-Trigger"] == "calculos-mudaram"
    banco.expire_all()
    assert obter_metricas(banco, sessao.id).investimento == Decimal("20000")


def test_metrica_vazia_apaga_o_valor(cliente_http, banco, sessao):
    salvar_metricas(banco, sessao.id, custo_hora=100)
    _metrica(cliente_http, sessao.id, "custo_hora", "")
    banco.expire_all()
    assert obter_metricas(banco, sessao.id).custo_hora is None


@pytest.mark.parametrize("valor", ["7.5", "abc", "-3"])
def test_metrica_invalida_e_recusada(cliente_http, banco, sessao, valor):
    resposta = _metrica(cliente_http, sessao.id, "horas_por_ocorrencia", valor)
    assert resposta.status_code == 422
    assert "Não salvo" in resposta.text
    assert "HX-Trigger" not in resposta.headers
    banco.expire_all()
    assert obter_metricas(banco, sessao.id) is None


def test_periodo_da_frequencia(cliente_http, banco, sessao):
    assert _metrica(cliente_http, sessao.id, "frequencia_periodo", "semana").status_code == 200
    banco.expire_all()
    assert obter_metricas(banco, sessao.id).frequencia_periodo == "semana"
    assert _metrica(cliente_http, sessao.id, "frequencia_periodo", "ano").status_code == 422


def test_metrica_desconhecida_da_404(cliente_http, sessao):
    assert _metrica(cliente_http, sessao.id, "sessao_id", "2").status_code == 404


def test_valor_gravado_aparece_no_campo_em_formato_brasileiro(cliente_http, banco, sessao):
    salvar_metricas(banco, sessao.id, investimento=Decimal("20000.00"))
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=9", headers=HX).text
    assert 'value="20.000"' in html


# --- Notas dos scores ---


def test_notas_de_dados_ficam_no_bloco_do_score(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=4", headers=HX).text
    for criterio in ("disponibilidade", "volume", "rotulos", "qualidade", "acesso_legal"):
        assert f'hx-post="/sessoes/{sessao.id}/notas/{criterio}"' in html
    assert "Exportável hoje" in html  # âncora da nota 3, vinda do YAML


def test_notas_finais_no_bloco_10_sem_a_nota_derivada(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=10", headers=HX).text
    assert f'hx-post="/sessoes/{sessao.id}/notas/dor_clara"' in html
    assert f'hx-post="/sessoes/{sessao.id}/notas/prontidao_dados"' not in html
    assert "Prontidão dos dados" in html  # aparece só para leitura


def test_origem_das_notas_finais_com_bloco_no_singular(cliente_http, sessao, questionario_v1):
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=10", headers=HX).text
    assert '<span class="discreto">(blocos 1)</span>' not in html
    for criterio in questionario_v1.scores.viabilidade_final.criterios:
        if criterio.id == questionario_v1.scores.prontidao_dados.criterio_final:
            continue  # nota derivada: não tem campo
        blocos = ", ".join(map(str, criterio.blocos_origem))
        palavra = "bloco" if len(criterio.blocos_origem) == 1 else "blocos"
        assert f'{criterio.rotulo} <span class="discreto">({palavra} {blocos})</span>' in html


def test_nota_salva_e_avisa_os_calculos(cliente_http, banco, sessao):
    resposta = _nota(cliente_http, sessao.id, "volume", "2")
    assert resposta.status_code == 200
    assert resposta.headers["HX-Trigger"] == "calculos-mudaram"
    assert notas_da_sessao(banco, sessao.id) == {"volume": 2}
    _nota(cliente_http, sessao.id, "volume", "")
    assert notas_da_sessao(banco, sessao.id) == {}


@pytest.mark.parametrize("valor", ["4", "-1", "x", "1,5"])
def test_nota_invalida_e_recusada(cliente_http, banco, sessao, valor):
    resposta = _nota(cliente_http, sessao.id, "volume", valor)
    assert resposta.status_code == 422
    assert notas_da_sessao(banco, sessao.id) == {}


def test_nota_derivada_nao_pode_ser_dada_a_mao(cliente_http, banco, sessao):
    resposta = _nota(cliente_http, sessao.id, "prontidao_dados", "2")
    assert resposta.status_code == 422
    assert "score de dados" in resposta.text
    assert notas_da_sessao(banco, sessao.id) == {}


def test_criterio_inexistente_da_404(cliente_http, sessao):
    assert _nota(cliente_http, sessao.id, "prazo", "2").status_code == 404


# --- Painel de cálculos ---


def test_painel_se_atualiza_quando_os_numeros_mudam(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}").text
    assert 'id="calculos"' in html
    assert f'hx-get="/sessoes/{sessao.id}/calculos"' in html
    assert "calculos-mudaram from:body" in html
    assert "sinais-mudaram from:body" in html


def test_painel_vazio_diz_o_que_falta(cliente_http, sessao):
    html = cliente_http.get(f"/sessoes/{sessao.id}/calculos", headers=HX).text
    assert "<html" not in html
    assert "falta" in html
    assert "Custo da hora" in html


def test_painel_com_o_caso_roberto(cliente_http, banco, sessao, caso_roberto):
    c = caso_roberto
    salvar_metricas(
        banco,
        sessao.id,
        horas_por_ocorrencia=c.horas_por_ocorrencia,
        frequencia_quantidade=c.frequencia_quantidade,
        frequencia_periodo=c.frequencia_periodo,
        custo_hora=c.custo_hora,
        horas_economizadas_mes=c.horas_economizadas_mes,
        investimento=c.investimento,
        custo_fixo_mes=c.custo_fixo_mes,
    )
    for criterio, nota in (c.notas_dados | c.notas_viabilidade).items():
        salvar_nota(banco, sessao.id, criterio, nota)
    for sinal in c.sinais_marcados:
        marcar_sinal(banco, sessao.id, sinal)
    html = cliente_http.get(f"/sessoes/{sessao.id}/calculos", headers=HX).text
    assert "60 h" in html
    assert "R$ 6.000,00" in html
    assert "R$ 400,00" in html
    assert "R$ 3.000,00" in html
    assert "7,7 meses" in html
    assert "4 de 15" in html
    assert "Fase 0" in html
    assert "12 de 18" in html
    assert "Seguir com fase 0" in html
    assert "5 sinais" in html


def test_payback_acima_de_12_meses_aparece_em_alerta(cliente_http, banco, sessao):
    salvar_metricas(
        banco,
        sessao.id,
        horas_economizadas_mes=10,
        custo_hora=100,
        investimento=26_000,
        custo_fixo_mes=0,
    )
    html = cliente_http.get(f"/sessoes/{sessao.id}/calculos", headers=HX).text
    assert "26 meses" in html
    assert "difícil de aprovar" in html


def test_projeto_que_nunca_se_paga(cliente_http, banco, sessao):
    salvar_metricas(
        banco,
        sessao.id,
        horas_economizadas_mes=1,
        custo_hora=100,
        investimento=1,
        custo_fixo_mes=400,
    )
    html = cliente_http.get(f"/sessoes/{sessao.id}/calculos", headers=HX).text
    assert "não se paga" in html


def test_nota_derivada_aparece_no_bloco_10(cliente_http, banco, sessao, caso_roberto):
    for criterio, nota in caso_roberto.notas_dados.items():
        salvar_nota(banco, sessao.id, criterio, nota)
    html = cliente_http.get(f"/sessoes/{sessao.id}?bloco=10", headers=HX).text
    assert "score de dados 4 de 15" in html


def test_dado_que_o_questionario_nao_reconhece_nao_derruba_a_tela(cliente_http, banco, sessao):
    # Um sinal gravado com id que não existe no questionário da sessão (dado antigo ou
    # corrompido): a página continua abrindo e o painel explica o problema.
    marcar_sinal(banco, sessao.id, "b1.s99")
    resposta = cliente_http.get(f"/sessoes/{sessao.id}")
    assert resposta.status_code == 200
    assert "Não foi possível calcular" in resposta.text
    assert "b1.s99" in resposta.text

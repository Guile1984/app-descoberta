"""Banco de demonstração com o caso Roberto (`uv run python -m descoberta.demo`)."""

from decimal import Decimal

import pytest
from sqlmodel import Session

from descoberta.demo import ANOTACOES, RESPOSTAS, main, popular_demo
from descoberta.dominio.payback import economia_mes, payback_meses
from descoberta.dominio.scores import (
    nota_prontidao_para_viabilidade,
    score_prontidao,
    score_viabilidade,
)
from descoberta.questionario import pergunta_visivel
from descoberta.repositorio import (
    CAMINHO_BANCO_PADRAO,
    anotacoes_da_sessao,
    criar_engine,
    listar_clientes,
    listar_sessoes,
    notas_da_sessao,
    obter_metricas,
    respostas_da_sessao,
    sinais_marcados,
)


@pytest.fixture
def banco_demo(tmp_path):
    caminho = tmp_path / "demo.db"
    popular_demo(caminho)
    engine = criar_engine(caminho)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _sessao(banco_demo):
    [cliente] = listar_clientes(banco_demo)
    [sessao] = listar_sessoes(banco_demo, cliente.id)
    return cliente, sessao


def test_cliente_e_sessao_do_roberto(banco_demo):
    cliente, sessao = _sessao(banco_demo)
    assert (cliente.nome, cliente.empresa, cliente.num_funcionarios) == (
        "Roberto",
        "Construtora Alvorada",
        35,
    )
    assert sessao.tipo_solucao == "visao_computacional"
    assert sessao.versao_questionario == 1


def test_numeros_batem_com_o_caso_de_referencia(banco_demo, caso_roberto, questionario_v1):
    _, sessao = _sessao(banco_demo)
    m = obter_metricas(banco_demo, sessao.id)
    assert m.horas_por_ocorrencia == caso_roberto.horas_por_ocorrencia
    assert m.frequencia_quantidade == caso_roberto.frequencia_quantidade
    assert m.frequencia_periodo == caso_roberto.frequencia_periodo
    assert m.custo_hora == caso_roberto.custo_hora
    assert m.horas_economizadas_mes == caso_roberto.horas_economizadas_mes
    assert m.investimento == caso_roberto.investimento
    assert m.custo_fixo_mes == caso_roberto.custo_fixo_mes

    notas = notas_da_sessao(banco_demo, sessao.id)
    assert notas == caso_roberto.notas_dados | caso_roberto.notas_viabilidade
    dados = score_prontidao(caso_roberto.notas_dados, questionario_v1)
    assert dados.pontuacao == 4
    final = score_viabilidade(
        caso_roberto.notas_viabilidade
        | {"prontidao_dados": nota_prontidao_para_viabilidade(dados.pontuacao, questionario_v1)},
        questionario_v1,
    )
    assert final.pontuacao == 12

    meses = payback_meses(
        m.investimento, economia_mes(m.horas_economizadas_mes, m.custo_hora), m.custo_fixo_mes
    )
    assert round(meses, 1) == Decimal("7.7")

    marcados = [sinal.sinal_id for sinal in sinais_marcados(banco_demo, sessao.id)]
    assert marcados == list(caso_roberto.sinais_marcados)


def test_respostas_existem_e_aparecem_para_visao_computacional(banco_demo, questionario_v1):
    _, sessao = _sessao(banco_demo)
    respostas = respostas_da_sessao(banco_demo, sessao.id)
    assert respostas == RESPOSTAS
    assert {"b4.vc1", "b4.vc2", "b4.vc3", "b4.vc4"} <= respostas.keys()
    for pergunta_id in respostas:
        assert pergunta_visivel(questionario_v1, pergunta_id, "visao_computacional")


def test_rodar_de_novo_recria_sem_duplicar(tmp_path):
    caminho = tmp_path / "demo.db"
    popular_demo(caminho)
    popular_demo(caminho)
    engine = criar_engine(caminho)
    with Session(engine) as session:
        assert len(listar_clientes(session)) == 1
    engine.dispose()


def test_recusa_o_banco_real():
    with pytest.raises(ValueError, match="banco real"):
        popular_demo(CAMINHO_BANCO_PADRAO)


def test_comando_cria_o_banco_e_explica_como_abrir(tmp_path, capsys):
    caminho = tmp_path / "demo.db"
    main([str(caminho)])
    assert caminho.exists()
    assert "DESCOBERTA_BANCO" in capsys.readouterr().out


def test_anotacoes_de_exemplo(banco_demo):
    _, sessao = _sessao(banco_demo)
    gravadas = [(a.texto, a.bloco) for a in anotacoes_da_sessao(banco_demo, sessao.id)]
    assert gravadas == ANOTACOES

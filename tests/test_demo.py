"""Banco de demonstração com o caso Roberto (`uv run python -m descoberta.demo`)."""

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from descoberta.demo import (
    ANOTACOES,
    ESCOPO,
    INDICADORES,
    PROXIMOS_PASSOS,
    RESPOSTAS,
    RISCOS,
    TEXTOS,
    main,
    popular_demo,
)
from descoberta.dominio.payback import economia_mes, payback_meses
from descoberta.dominio.proposta import investimento_total, itens_repetidos
from descoberta.dominio.revisao import pendencias_da_revisao
from descoberta.dominio.scores import (
    nota_prontidao_para_viabilidade,
    score_prontidao,
    score_viabilidade,
)
from descoberta.questionario import pergunta_visivel
from descoberta.repositorio import (
    CAMINHO_BANCO_PADRAO,
    FaseProposta,
    Indicador,
    ItemEscopo,
    ItemProposta,
    ProximoPasso,
    Risco,
    anotacoes_da_sessao,
    criar_engine,
    itens_da_sessao,
    listar_clientes,
    listar_sessoes,
    notas_da_sessao,
    obter_metricas,
    obter_perfil,
    obter_proposta,
    respostas_da_sessao,
    sinais_marcados,
    textos_da_sessao,
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
    itens_do_encerramento = {item.id for item in questionario_v1.encerramento.itens}
    assert itens_do_encerramento <= respostas.keys()
    for pergunta_id in respostas.keys() - itens_do_encerramento:
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


def test_saidas_da_revisao_do_roberto(banco_demo, questionario_v1):
    _, sessao = _sessao(banco_demo)
    riscos = itens_da_sessao(banco_demo, Risco, sessao.id)
    indicadores = itens_da_sessao(banco_demo, Indicador, sessao.id)
    escopo = itens_da_sessao(banco_demo, ItemEscopo, sessao.id)
    passos = itens_da_sessao(banco_demo, ProximoPasso, sessao.id)
    textos = textos_da_sessao(banco_demo, sessao.id)
    assert len(riscos) == len(RISCOS)
    assert len(indicadores) == len(INDICADORES)
    assert len(escopo) == len(ESCOPO)
    assert len(passos) == len(PROXIMOS_PASSOS)
    assert textos == TEXTOS

    categorias = {c.id for c in questionario_v1.revisao.categorias_risco}
    assert {r.categoria for r in riscos} <= categorias
    assert set(TEXTOS) == {t.id for t in questionario_v1.revisao.textos}

    pendencias = pendencias_da_revisao(
        [t.id for t in questionario_v1.revisao.textos], textos, riscos, indicadores, escopo, passos
    )
    assert pendencias.total == 0


def test_textos_do_demo_revisados():
    assert "Roberto" in RESPOSTAS["b1.o6"]
    assert "investimento" in RESPOSTAS["b1.o6"]
    assert "eu entrego" not in RESPOSTAS["enc.proximos_passos"]
    assert "o consultor entrega" in RESPOSTAS["enc.proximos_passos"]
    assert "a partir de 6" in TEXTOS["recomendacao"]


def test_proximos_passos_vencem_depois_da_criacao_do_demo(tmp_path):
    caminho = tmp_path / "demo.db"
    sessao_id = popular_demo(caminho, hoje=date(2027, 3, 1))
    engine = criar_engine(caminho)
    with Session(engine) as session:
        prazos = [p.prazo for p in itens_da_sessao(session, ProximoPasso, sessao_id)]
    engine.dispose()
    assert prazos == sorted(prazos)
    assert all(prazo > date(2027, 3, 1) for prazo in prazos)


def test_consultor_ficticio_com_logotipo(banco_demo):
    perfil = obter_perfil(banco_demo)
    assert perfil.dados_ficticios is True
    assert perfil.cpf_cnpj == "11.222.333/0001-81"
    assert perfil.email.endswith("@example.com")  # domínio reservado para exemplos
    assert perfil.logotipo.startswith(b"\x89PNG")


def test_proposta_do_demo(banco_demo):
    _, sessao = _sessao(banco_demo)
    proposta = obter_proposta(banco_demo, sessao.id)
    assert (proposta.cliente_cidade, proposta.cliente_uf) == ("Campinas", "SP")

    fases = itens_da_sessao(banco_demo, FaseProposta, sessao.id)
    assert [f.investimento for f in fases] == [Decimal("6000"), Decimal("14000")]
    # O total é o investimento da métrica, o mesmo do payback do relatório.
    total = investimento_total([f.investimento for f in fases])
    assert total == obter_metricas(banco_demo, sessao.id).investimento

    escopo = itens_da_sessao(banco_demo, ItemProposta, sessao.id, tipo="escopo")
    por_fase = [(f.nome, [i.texto for i in escopo if i.fase_id == f.id]) for f in fases]
    assert itens_repetidos(por_fase) == []
    fase_0, mvp = (textos for _, textos in por_fase)
    assert any(t.startswith("Guia de captura de fotos") for t in fase_0)
    assert any(t.startswith("Organização e rotulagem das cerca de 500 fotos") for t in fase_0)
    assert all(t.startswith(("Triagem", "Envio")) for t in mvp)


def test_pessoas_citadas_do_demo(banco_demo):
    from descoberta.demo import PESSOAS_CITADAS
    from descoberta.repositorio import pessoas_citadas

    _, sessao = _sessao(banco_demo)
    assert [p.nome for p in pessoas_citadas(banco_demo, sessao.id)] == PESSOAS_CITADAS == ["Marcos"]

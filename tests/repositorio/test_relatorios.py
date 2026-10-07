import pytest

from descoberta.repositorio import (
    OrigemRelatorio,
    RegistroNaoEncontrado,
    listar_relatorios,
    obter_relatorio,
    salvar_relatorio,
)


def test_salvar_relatorio_por_template(session, sessao):
    relatorio = salvar_relatorio(
        session, sessao.id, origem="template", conteudo="# Relatório de Descoberta"
    )
    lido = obter_relatorio(session, relatorio.id)
    assert lido.origem == OrigemRelatorio.template
    assert lido.conteudo == "# Relatório de Descoberta"
    assert lido.modelo is None
    assert lido.versao_prompt is None
    assert lido.criado_em is not None


def test_salvar_relatorio_por_llm_guarda_modelo_e_prompt(session, sessao):
    relatorio = salvar_relatorio(
        session,
        sessao.id,
        origem=OrigemRelatorio.llm,
        conteudo="Rascunho",
        modelo="claude-opus-5-5",
        versao_prompt="relatorio_v1",
    )
    lido = obter_relatorio(session, relatorio.id)
    assert lido.modelo == "claude-opus-5-5"
    assert lido.versao_prompt == "relatorio_v1"


@pytest.mark.parametrize(
    "faltando", [{"modelo": "claude-opus-5-5"}, {"versao_prompt": "relatorio_v1"}]
)
def test_relatorio_por_llm_exige_modelo_e_versao_do_prompt(session, sessao, faltando):
    with pytest.raises(ValueError, match="modelo e versão do prompt"):
        salvar_relatorio(session, sessao.id, origem="llm", conteudo="Rascunho", **faltando)


def test_origem_invalida(session, sessao):
    with pytest.raises(ValueError, match="origem"):
        salvar_relatorio(session, sessao.id, origem="manual", conteudo="Texto")


def test_conteudo_vazio(session, sessao):
    with pytest.raises(ValueError, match="conteudo"):
        salvar_relatorio(session, sessao.id, origem="template", conteudo="  ")


def test_listar_mais_recente_primeiro(session, sessao):
    primeiro = salvar_relatorio(session, sessao.id, origem="template", conteudo="v1")
    segundo = salvar_relatorio(session, sessao.id, origem="template", conteudo="v2")
    assert [r.id for r in listar_relatorios(session, sessao.id)] == [segundo.id, primeiro.id]


def test_obter_inexistente(session):
    assert obter_relatorio(session, 999) is None


def test_relatorio_em_sessao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        salvar_relatorio(session, 999, origem="template", conteudo="Texto")

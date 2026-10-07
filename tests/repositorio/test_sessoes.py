from datetime import date, datetime

import pytest

from descoberta.repositorio import (
    RegistroNaoEncontrado,
    StatusSessao,
    atualizar_sessao,
    criar_cliente,
    criar_sessao,
    excluir_sessao,
    listar_sessoes,
    obter_cliente,
    obter_sessao,
    respostas_da_sessao,
    salvar_resposta,
)


def test_criar_com_valores_padrao(session, sessao, cliente):
    lido = obter_sessao(session, sessao.id)
    assert lido.cliente_id == cliente.id
    assert lido.data == date(2026, 10, 7)
    assert lido.versao_questionario == 1
    assert lido.status == StatusSessao.preparacao
    assert lido.tipo_solucao is None
    assert lido.contexto_previo is None
    assert lido.amostra_dados_recebida is False


def test_criar_com_todos_os_campos(session, cliente):
    sessao = criar_sessao(
        session,
        cliente_id=cliente.id,
        data=date(2026, 10, 7),
        versao_questionario=1,
        tipo_solucao="visao_computacional",
        contexto_previo="Indicação de um parceiro.",
        amostra_dados_recebida=True,
    )
    lido = obter_sessao(session, sessao.id)
    assert lido.tipo_solucao == "visao_computacional"
    assert lido.contexto_previo == "Indicação de um parceiro."
    assert lido.amostra_dados_recebida is True


def test_criar_para_cliente_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado, match="cliente 999"):
        criar_sessao(session, cliente_id=999, data=date(2026, 10, 7), versao_questionario=1)


@pytest.mark.parametrize(
    ("campos", "excecao", "erro"),
    [
        ({"versao_questionario": 0}, ValueError, "versao_questionario"),
        ({"data": datetime(2026, 10, 7, 9, 0)}, TypeError, "data"),
        ({"data": "2026-10-07"}, TypeError, "data"),
        ({"tipo_solucao": "Visão Computacional"}, ValueError, "tipo_solucao"),
        ({"status": "pausada"}, ValueError, "status"),
        ({"amostra_dados_recebida": "sim"}, TypeError, "amostra_dados_recebida"),
    ],
)
def test_valores_invalidos(session, cliente, campos, excecao, erro):
    dados = {"data": date(2026, 10, 7), "versao_questionario": 1} | campos
    with pytest.raises(excecao, match=erro):
        criar_sessao(session, cliente_id=cliente.id, **dados)


def test_listar_sessoes_do_cliente_mais_recente_primeiro(session, cliente, sessao):
    outra = criar_sessao(
        session, cliente_id=cliente.id, data=date(2026, 11, 1), versao_questionario=1
    )
    ana = criar_cliente(session, nome="Ana", empresa="Padaria Sol")
    criar_sessao(session, cliente_id=ana.id, data=date(2026, 12, 1), versao_questionario=1)

    assert [s.id for s in listar_sessoes(session, cliente.id)] == [outra.id, sessao.id]


def test_atualizar(session, sessao):
    atualizar_sessao(
        session,
        sessao.id,
        tipo_solucao="llm_rag",
        status="em_andamento",
        amostra_dados_recebida=True,
    )
    lido = obter_sessao(session, sessao.id)
    assert lido.tipo_solucao == "llm_rag"
    assert lido.status == StatusSessao.em_andamento
    assert lido.amostra_dados_recebida is True
    assert lido.versao_questionario == 1


def test_atualizar_tipo_solucao_para_nenhum(session, sessao):
    atualizar_sessao(session, sessao.id, tipo_solucao="visao_computacional")
    atualizar_sessao(session, sessao.id, tipo_solucao=None)
    assert obter_sessao(session, sessao.id).tipo_solucao is None


def test_versao_do_questionario_nao_muda(session, sessao):
    # A sessão fica presa à versão do questionário com que foi aberta.
    with pytest.raises(ValueError, match="campo desconhecido 'versao_questionario'"):
        atualizar_sessao(session, sessao.id, versao_questionario=2)


def test_status_gravado_como_texto_legivel(session, sessao):
    from sqlalchemy import text

    atualizar_sessao(session, sessao.id, status=StatusSessao.concluida)
    assert session.exec(text("SELECT status FROM sessao")).one()[0] == "concluida"


def test_excluir_apaga_registros_mas_nao_o_cliente(session, cliente, sessao):
    salvar_resposta(session, sessao.id, "b1.o1", "Texto.")
    excluir_sessao(session, sessao.id)
    assert obter_sessao(session, sessao.id) is None
    assert respostas_da_sessao(session, sessao.id) == {}
    assert obter_cliente(session, cliente.id) is not None


def test_excluir_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado, match="sessão 999"):
        excluir_sessao(session, 999)

"""Respostas, sinais de alerta marcados e anotações livres de uma sessão."""

import pytest
from sqlmodel import select

from descoberta.repositorio import (
    RegistroNaoEncontrado,
    Resposta,
    adicionar_anotacao,
    anotacoes_da_sessao,
    anotar_sinal,
    desmarcar_sinal,
    editar_anotacao,
    excluir_anotacao,
    marcar_sinal,
    respostas_da_sessao,
    salvar_resposta,
    sinais_marcados,
)

# --- Respostas ---


def test_salvar_resposta(session, sessao):
    salvar_resposta(session, sessao.id, "b1.o1", "Orçamentos levam 4 horas.")
    assert respostas_da_sessao(session, sessao.id) == {"b1.o1": "Orçamentos levam 4 horas."}


def test_salvar_de_novo_atualiza_sem_duplicar(session, sessao):
    salvar_resposta(session, sessao.id, "b1.o1", "Rascunho")
    salvar_resposta(session, sessao.id, "b1.o1", "Versão final")
    assert respostas_da_sessao(session, sessao.id) == {"b1.o1": "Versão final"}
    assert len(session.exec(select(Resposta)).all()) == 1


def test_ids_do_yaml_guardados_como_estao(session, sessao):
    for id_ in ("b1.o1", "b2.o1", "b4.vc1"):
        salvar_resposta(session, sessao.id, id_, f"resposta {id_}")
    session.expire_all()
    assert set(respostas_da_sessao(session, sessao.id)) == {"b1.o1", "b2.o1", "b4.vc1"}


def test_texto_da_resposta_guardado_como_digitado(session, sessao):
    texto = "  Linha 1\nLinha 2  "
    salvar_resposta(session, sessao.id, "b1.o1", texto)
    assert respostas_da_sessao(session, sessao.id)["b1.o1"] == texto


@pytest.mark.parametrize("vazio", ["", "   \n"])
def test_resposta_vazia_apaga(session, sessao, vazio):
    salvar_resposta(session, sessao.id, "b1.o1", "Texto")
    assert salvar_resposta(session, sessao.id, "b1.o1", vazio) is None
    assert respostas_da_sessao(session, sessao.id) == {}


def test_resposta_vazia_sem_resposta_anterior(session, sessao):
    assert salvar_resposta(session, sessao.id, "b1.o1", "") is None


def test_respostas_separadas_por_sessao(session, sessao, cliente):
    from datetime import date

    from descoberta.repositorio import criar_sessao

    outra = criar_sessao(
        session, cliente_id=cliente.id, data=date(2026, 11, 1), versao_questionario=1
    )
    salvar_resposta(session, sessao.id, "b1.o1", "Primeira")
    salvar_resposta(session, outra.id, "b1.o1", "Segunda")
    assert respostas_da_sessao(session, sessao.id) == {"b1.o1": "Primeira"}
    assert respostas_da_sessao(session, outra.id) == {"b1.o1": "Segunda"}


@pytest.mark.parametrize("id_invalido", ["", "B1.O1", " b1.o1", "b1 o1"])
def test_id_de_pergunta_invalido(session, sessao, id_invalido):
    with pytest.raises(ValueError, match="pergunta_id"):
        salvar_resposta(session, sessao.id, id_invalido, "Texto")


def test_resposta_em_sessao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado, match="sessão 999"):
        salvar_resposta(session, 999, "b1.o1", "Texto")


# --- Sinais de alerta ---


def test_marcar_sinal(session, sessao):
    marcar_sinal(session, sessao.id, "b2.s3", observacao="Ninguém registra as medições.")
    (sinal,) = sinais_marcados(session, sessao.id)
    assert sinal.sinal_id == "b2.s3"
    assert sinal.observacao == "Ninguém registra as medições."
    assert sinal.marcado_em is not None


def test_marcar_duas_vezes_fica_um_so(session, sessao):
    marcar_sinal(session, sessao.id, "b2.s3")
    marcar_sinal(session, sessao.id, "b2.s3", observacao="Detalhe depois.")
    (sinal,) = sinais_marcados(session, sessao.id)
    assert sinal.observacao == "Detalhe depois."


def test_marcar_de_novo_sem_observacao_mantem_a_anterior(session, sessao):
    marcar_sinal(session, sessao.id, "b2.s3", observacao="Detalhe.")
    marcar_sinal(session, sessao.id, "b2.s3")
    assert sinais_marcados(session, sessao.id)[0].observacao == "Detalhe."


def test_sinais_na_ordem_em_que_foram_marcados(session, sessao):
    for id_ in ("b9.s1", "b1.s4", "b2.s2"):
        marcar_sinal(session, sessao.id, id_)
    assert [s.sinal_id for s in sinais_marcados(session, sessao.id)] == [
        "b9.s1",
        "b1.s4",
        "b2.s2",
    ]


def test_desmarcar(session, sessao):
    marcar_sinal(session, sessao.id, "b2.s3")
    marcar_sinal(session, sessao.id, "b1.s4")
    desmarcar_sinal(session, sessao.id, "b2.s3")
    assert [s.sinal_id for s in sinais_marcados(session, sessao.id)] == ["b1.s4"]


def test_desmarcar_sinal_nao_marcado_nao_faz_nada(session, sessao):
    desmarcar_sinal(session, sessao.id, "b2.s3")
    assert sinais_marcados(session, sessao.id) == []


def test_id_de_sinal_invalido(session, sessao):
    with pytest.raises(ValueError, match="sinal_id"):
        marcar_sinal(session, sessao.id, "B2.S3")


# --- Anotações livres ---


def test_anotacao_com_e_sem_bloco(session, sessao):
    adicionar_anotacao(session, sessao.id, "Cliente chegou atrasado.")
    adicionar_anotacao(session, sessao.id, "Planilha de medições existe.", bloco=4)
    anotacoes = anotacoes_da_sessao(session, sessao.id)
    assert [(a.bloco, a.texto) for a in anotacoes] == [
        (None, "Cliente chegou atrasado."),
        (4, "Planilha de medições existe."),
    ]
    assert all(a.criado_em is not None for a in anotacoes)


def test_editar_anotacao(session, sessao):
    anotacao = adicionar_anotacao(session, sessao.id, "Rascunho", bloco=2)
    editar_anotacao(session, anotacao.id, "Texto revisado")
    (lida,) = anotacoes_da_sessao(session, sessao.id)
    assert lida.texto == "Texto revisado"
    assert lida.bloco == 2


def test_excluir_anotacao(session, sessao):
    anotacao = adicionar_anotacao(session, sessao.id, "Apagar")
    excluir_anotacao(session, anotacao.id)
    assert anotacoes_da_sessao(session, sessao.id) == []


@pytest.mark.parametrize(
    ("texto", "bloco", "excecao", "erro"),
    [
        ("", None, ValueError, "texto"),
        ("   ", None, ValueError, "texto"),
        ("Ok", 0, ValueError, "bloco"),
        ("Ok", "4", TypeError, "bloco"),
    ],
)
def test_anotacao_invalida(session, sessao, texto, bloco, excecao, erro):
    with pytest.raises(excecao, match=erro):
        adicionar_anotacao(session, sessao.id, texto, bloco=bloco)


def test_editar_anotacao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado, match="anotação 999"):
        editar_anotacao(session, 999, "Texto")


def test_resposta_precisa_ser_texto(session, sessao):
    with pytest.raises(TypeError, match="texto"):
        salvar_resposta(session, sessao.id, "b1.o1", None)


# --- Observação do sinal (Sprint 5) ---


def test_anotar_sinal_grava_e_apaga_a_observacao(session, sessao):
    marcar_sinal(session, sessao.id, "b9.s1", observacao="Antiga")
    anotar_sinal(session, sessao.id, "b9.s1", "  Nova  ")
    assert sinais_marcados(session, sessao.id)[0].observacao == "Nova"
    anotar_sinal(session, sessao.id, "b9.s1", "")
    assert sinais_marcados(session, sessao.id)[0].observacao is None


def test_anotar_sinal_nao_marcado_gera_erro(session, sessao):
    with pytest.raises(RegistroNaoEncontrado):
        anotar_sinal(session, sessao.id, "b9.s1", "x")
    assert sinais_marcados(session, sessao.id) == []

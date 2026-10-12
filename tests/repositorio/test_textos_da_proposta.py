"""Textos narrativos da proposta (tabela própria) e rascunhos aceitos na proposta."""

from decimal import Decimal

import pytest

from descoberta.proposta.inicial import FaseInicial, PropostaInicial
from descoberta.repositorio import (
    DestinoRascunho,
    FaseProposta,
    RegistroNaoEncontrado,
    SituacaoRascunho,
    aceitar_rascunho_da_proposta,
    criar_proposta,
    excluir_proposta,
    itens_da_sessao,
    registrar_rascunho,
    salvar_texto_proposta,
    textos_da_proposta,
)

INICIAL = PropostaInicial(
    15,
    "50%",
    "Inclusos",
    "IPCA",
    [FaseInicial("MVP", "Construir", 8, Decimal("1"), [], [])],
    [],
    [],
    [],
)
GERADO = {"provedor": "falso", "modelo": "falso-1", "versao_prompt": "rascunho_proposta_v1"}


@pytest.fixture
def com_proposta(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    return sessao


def test_salvar_e_apagar_o_contexto(session, com_proposta):
    salvar_texto_proposta(session, com_proposta.id, "contexto", "  A Alvorada precisa…  ")
    assert textos_da_proposta(session, com_proposta.id) == {"contexto": "A Alvorada precisa…"}
    salvar_texto_proposta(session, com_proposta.id, "contexto", "   ")
    assert textos_da_proposta(session, com_proposta.id) == {}


def test_campo_desconhecido(session, com_proposta):
    with pytest.raises(ValueError, match="campo"):
        salvar_texto_proposta(session, com_proposta.id, "outro", "x")


def test_sem_proposta(session, sessao):
    with pytest.raises(RegistroNaoEncontrado, match="proposta"):
        salvar_texto_proposta(session, sessao.id, "contexto", "x")


def test_aceitar_o_contexto(session, com_proposta):
    salvar_texto_proposta(session, com_proposta.id, "contexto", "Antigo.")
    rascunho = registrar_rascunho(
        session,
        com_proposta.id,
        destino=DestinoRascunho.proposta,
        campo="contexto",
        texto="Novo contexto.",
        **GERADO,
    )
    aceitar_rascunho_da_proposta(session, rascunho.id)
    assert textos_da_proposta(session, com_proposta.id) == {"contexto": "Novo contexto."}
    session.refresh(rascunho)
    assert rascunho.situacao is SituacaoRascunho.aceito


def test_aceitar_o_objetivo_da_fase(session, com_proposta):
    [fase] = itens_da_sessao(session, FaseProposta, com_proposta.id)
    rascunho = registrar_rascunho(
        session,
        com_proposta.id,
        destino=DestinoRascunho.proposta,
        campo=f"objetivo_fase.{fase.id}",
        texto="Validar a triagem no processo real.",
        **GERADO,
    )
    aceitar_rascunho_da_proposta(session, rascunho.id)
    session.refresh(fase)
    assert fase.objetivo == "Validar a triagem no processo real."


@pytest.mark.parametrize("campo", ["objetivo_fase.999", "objetivo_fase.x", "outro"])
def test_aceitar_campo_invalido(session, com_proposta, campo):
    rascunho = registrar_rascunho(
        session, com_proposta.id, destino=DestinoRascunho.proposta, campo=campo, texto="x", **GERADO
    )
    with pytest.raises((ValueError, RegistroNaoEncontrado)):
        aceitar_rascunho_da_proposta(session, rascunho.id)
    session.refresh(rascunho)
    assert rascunho.situacao is SituacaoRascunho.pendente


def test_aceitar_fase_de_outra_sessao(session, com_proposta, outra_sessao):
    criar_proposta(session, outra_sessao.id, INICIAL, versao_modelo=1)
    [fase_alheia] = itens_da_sessao(session, FaseProposta, outra_sessao.id)
    rascunho = registrar_rascunho(
        session,
        com_proposta.id,
        destino=DestinoRascunho.proposta,
        campo=f"objetivo_fase.{fase_alheia.id}",
        texto="x",
        **GERADO,
    )
    with pytest.raises(RegistroNaoEncontrado):
        aceitar_rascunho_da_proposta(session, rascunho.id)


def test_aceitar_rascunho_da_revisao_na_proposta(session, com_proposta):
    rascunho = registrar_rascunho(
        session,
        com_proposta.id,
        destino=DestinoRascunho.revisao,
        campo="recomendacao",
        texto="x",
        **GERADO,
    )
    with pytest.raises(ValueError, match="proposta"):
        aceitar_rascunho_da_proposta(session, rascunho.id)


def test_recriar_apaga_os_textos(session, com_proposta):
    salvar_texto_proposta(session, com_proposta.id, "contexto", "Texto.")
    excluir_proposta(session, com_proposta.id)
    assert textos_da_proposta(session, com_proposta.id) == {}

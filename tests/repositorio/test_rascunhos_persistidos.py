"""Rascunhos do LLM, pessoas citadas e prévia confirmada, no banco.

O rascunho fica numa tabela própria e nunca sobrescreve o texto do consultor sozinho: só
"aceitar" copia o texto, numa transação junto com a marcação do rascunho.
"""

from decimal import Decimal

import pytest
from sqlmodel import select

from descoberta.proposta.inicial import FaseInicial, PropostaInicial
from descoberta.repositorio import (
    DestinoRascunho,
    FaseProposta,
    PessoaCitada,
    Rascunho,
    RegistroNaoEncontrado,
    SituacaoRascunho,
    aceitar_rascunho_da_revisao,
    adicionar_pessoa_citada,
    confirmar_previa,
    criar_proposta,
    descartar_rascunho,
    excluir_proposta,
    excluir_sessao,
    itens_da_sessao,
    pessoas_citadas,
    previa_confirmada,
    rascunho_pendente,
    rascunhos_da_sessao,
    registrar_rascunho,
    remover_pessoa_citada,
    salvar_texto_secao,
    textos_da_sessao,
)

GERADO = {
    "texto": "Rascunho do resumo.",
    "provedor": "claude",
    "modelo": "claude-opus-5-5",
    "versao_prompt": "rascunho_revisao_v1",
}


def _registrar(session, sessao_id, campo="resumo_executivo", **mudancas):
    dados = {**GERADO, **mudancas}
    return registrar_rascunho(
        session, sessao_id, destino=DestinoRascunho.revisao, campo=campo, **dados
    )


# --- Rascunhos ---


def test_registrar_guarda_modelo_e_versao_do_prompt(session, sessao):
    rascunho = _registrar(session, sessao.id, alertas=["Confira [PESSOA_9]."])
    assert rascunho.id is not None
    assert rascunho.situacao is SituacaoRascunho.pendente
    assert (rascunho.provedor, rascunho.modelo, rascunho.versao_prompt) == (
        "claude",
        "claude-opus-5-5",
        "rascunho_revisao_v1",
    )
    assert rascunho.lista_de_alertas == ["Confira [PESSOA_9]."]
    assert rascunho.decidido_em is None


def test_registrar_nao_mexe_no_texto_do_consultor(session, sessao):
    salvar_texto_secao(session, sessao.id, "resumo_executivo", "Texto do consultor.")
    _registrar(session, sessao.id)
    assert textos_da_sessao(session, sessao.id)["resumo_executivo"] == "Texto do consultor."


def test_rascunho_novo_substitui_o_pendente_do_mesmo_campo(session, sessao):
    primeiro = _registrar(session, sessao.id, texto="Primeiro.")
    outro_campo = _registrar(session, sessao.id, campo="recomendacao")
    segundo = _registrar(session, sessao.id, texto="Segundo.")
    session.refresh(primeiro)
    assert primeiro.situacao is SituacaoRascunho.substituido
    assert rascunho_pendente(session, sessao.id, DestinoRascunho.revisao, "resumo_executivo") == (
        segundo
    )
    session.refresh(outro_campo)
    assert outro_campo.situacao is SituacaoRascunho.pendente


def test_aceitar_copia_o_texto_e_marca(session, sessao):
    salvar_texto_secao(session, sessao.id, "resumo_executivo", "Texto antigo.")
    rascunho = _registrar(session, sessao.id)
    aceitar_rascunho_da_revisao(session, rascunho.id)
    assert textos_da_sessao(session, sessao.id)["resumo_executivo"] == "Rascunho do resumo."
    session.refresh(rascunho)
    assert rascunho.situacao is SituacaoRascunho.aceito
    assert rascunho.decidido_em is not None
    assert rascunho_pendente(session, sessao.id, DestinoRascunho.revisao, "resumo_executivo") is (
        None
    )


def test_aceitar_texto_novo(session, sessao):
    rascunho = _registrar(session, sessao.id, campo="recomendacao", texto="Seguir com fase 0.")
    aceitar_rascunho_da_revisao(session, rascunho.id)
    assert textos_da_sessao(session, sessao.id) == {"recomendacao": "Seguir com fase 0."}


def test_descartar_so_marca(session, sessao):
    salvar_texto_secao(session, sessao.id, "resumo_executivo", "Texto do consultor.")
    rascunho = _registrar(session, sessao.id)
    descartar_rascunho(session, rascunho.id)
    session.refresh(rascunho)
    assert rascunho.situacao is SituacaoRascunho.descartado
    assert textos_da_sessao(session, sessao.id)["resumo_executivo"] == "Texto do consultor."


@pytest.mark.parametrize("decidir", [aceitar_rascunho_da_revisao, descartar_rascunho])
def test_rascunho_ja_decidido_nao_muda(session, sessao, decidir):
    rascunho = _registrar(session, sessao.id)
    descartar_rascunho(session, rascunho.id)
    with pytest.raises(ValueError, match="já foi"):
        decidir(session, rascunho.id)


def test_aceitar_na_revisao_so_rascunho_da_revisao(session, sessao):
    rascunho = registrar_rascunho(
        session, sessao.id, destino=DestinoRascunho.proposta, campo="contexto", **GERADO
    )
    with pytest.raises(ValueError, match="revisão"):
        aceitar_rascunho_da_revisao(session, rascunho.id)


def test_rascunho_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        descartar_rascunho(session, 999)


@pytest.mark.parametrize(
    ("mudancas", "erro"),
    [
        ({"texto": "   "}, "texto"),
        ({"modelo": ""}, "modelo"),
        ({"versao_prompt": ""}, "versao_prompt"),
        ({"campo": "Resumo Executivo"}, "campo"),
    ],
)
def test_registrar_invalido(session, sessao, mudancas, erro):
    with pytest.raises(ValueError, match=erro):
        _registrar(session, sessao.id, **mudancas)


def test_sessao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        _registrar(session, 999)


def test_lista_por_destino_e_situacao(session, sessao, outra_sessao):
    a = _registrar(session, sessao.id)
    b = registrar_rascunho(
        session, sessao.id, destino=DestinoRascunho.proposta, campo="contexto", **GERADO
    )
    _registrar(session, outra_sessao.id)
    descartar_rascunho(session, a.id)
    assert rascunhos_da_sessao(session, sessao.id) == [a, b]
    assert rascunhos_da_sessao(session, sessao.id, destino=DestinoRascunho.proposta) == [b]
    assert rascunhos_da_sessao(session, sessao.id, situacao=SituacaoRascunho.pendente) == [b]


def test_recriar_a_proposta_descarta_os_rascunhos_pendentes_dela(session, sessao):
    inicial = PropostaInicial(15, "50%", "Inclusos", "IPCA", [], [], [], [])
    criar_proposta(session, sessao.id, inicial, versao_modelo=1)
    da_proposta = registrar_rascunho(
        session, sessao.id, destino=DestinoRascunho.proposta, campo="contexto", **GERADO
    )
    da_revisao = _registrar(session, sessao.id)
    excluir_proposta(session, sessao.id)
    session.refresh(da_proposta)
    session.refresh(da_revisao)
    assert da_proposta.situacao is SituacaoRascunho.descartado
    assert da_revisao.situacao is SituacaoRascunho.pendente


def test_objetivo_da_fase_como_campo(session, sessao):
    fases = [FaseInicial("MVP", "Construir", 8, Decimal("1"), [], [])]
    criar_proposta(
        session, sessao.id, PropostaInicial(15, "x", "y", "z", fases, [], [], []), versao_modelo=1
    )
    [fase] = itens_da_sessao(session, FaseProposta, sessao.id)
    campo = f"objetivo_fase.{fase.id}"
    rascunho = registrar_rascunho(
        session, sessao.id, destino=DestinoRascunho.proposta, campo=campo, **GERADO
    )
    assert rascunho.campo == campo


# --- Pessoas citadas ---


def test_lista_de_pessoas(session, sessao, outra_sessao):
    marcos = adicionar_pessoa_citada(session, sessao.id, "  Marcos ")
    adicionar_pessoa_citada(session, sessao.id, "Cida")
    adicionar_pessoa_citada(session, outra_sessao.id, "Outra Pessoa")
    assert marcos.nome == "Marcos"
    assert [p.nome for p in pessoas_citadas(session, sessao.id)] == ["Marcos", "Cida"]
    remover_pessoa_citada(session, marcos.id)
    assert [p.nome for p in pessoas_citadas(session, sessao.id)] == ["Cida"]


def test_pessoa_repetida_nao_duplica(session, sessao):
    primeira = adicionar_pessoa_citada(session, sessao.id, "Cida")
    assert adicionar_pessoa_citada(session, sessao.id, "CIDA") == primeira
    assert adicionar_pessoa_citada(session, sessao.id, "Cída") == primeira
    assert len(pessoas_citadas(session, sessao.id)) == 1


@pytest.mark.parametrize("nome", ["", "   ", "A"])
def test_pessoa_invalida(session, sessao, nome):
    with pytest.raises(ValueError, match="nome"):
        adicionar_pessoa_citada(session, sessao.id, nome)


def test_remover_pessoa_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        remover_pessoa_citada(session, 999)


# --- Prévia confirmada ---


def test_previa_vale_para_a_mesma_impressao(session, sessao):
    assert not previa_confirmada(session, sessao.id, "abc")
    confirmar_previa(session, sessao.id, "abc")
    assert previa_confirmada(session, sessao.id, "abc")
    # A lista de pessoas ou um dado do cliente mudou: a prévia precisa ser vista de novo.
    assert not previa_confirmada(session, sessao.id, "def")
    confirmar_previa(session, sessao.id, "def")
    assert previa_confirmada(session, sessao.id, "def")


def test_previa_exige_impressao(session, sessao):
    with pytest.raises(ValueError, match="impressao"):
        confirmar_previa(session, sessao.id, "  ")


# --- Excluir a sessão leva tudo junto ---


def test_excluir_sessao_apaga_rascunhos_pessoas_e_previa(session, sessao):
    _registrar(session, sessao.id)
    adicionar_pessoa_citada(session, sessao.id, "Marcos")
    confirmar_previa(session, sessao.id, "abc")
    excluir_sessao(session, sessao.id)
    session.expire_all()
    assert session.exec(select(Rascunho)).all() == []
    assert session.exec(select(PessoaCitada)).all() == []
    assert not previa_confirmada(session, sessao.id, "abc")

"""Versões da proposta registradas como enviadas: PDF, hashes e Condições Gerais congeladas."""

import hashlib
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from descoberta.repositorio import (
    VersaoProposta,
    excluir_proposta,
    excluir_sessao,
    obter_versao_proposta,
    proximo_numero_versao_proposta,
    registrar_versao_proposta,
    versoes_da_proposta,
)

EMITIDO = datetime(2026, 10, 11, 14, 5, tzinfo=UTC)
CLAUSULAS = [{"id": "foro", "titulo": "Foro", "texto": "Foro de São Paulo/SP."}]


def _registrar(session, sessao_id, numero=1, conteudo="# Proposta\n", pdf=b"%PDF-p"):
    return registrar_versao_proposta(
        session,
        sessao_id,
        numero=numero,
        emitido_em=EMITIDO,
        conteudo_md=conteudo,
        pdf=pdf,
        versao_modelo=1,
        clausulas=CLAUSULAS,
    )


def test_registrar_guarda_pdf_hashes_e_clausulas(session, sessao):
    _registrar(session, sessao.id)
    session.expire_all()
    versao = obter_versao_proposta(session, sessao.id, 1)
    assert versao.pdf == b"%PDF-p"
    assert versao.hash_conteudo == hashlib.sha256(b"# Proposta\n").hexdigest()
    assert versao.hash_pdf == hashlib.sha256(b"%PDF-p").hexdigest()
    assert versao.versao_modelo == 1
    assert versao.clausulas == CLAUSULAS
    assert versao.emitido_em.replace(tzinfo=UTC) == EMITIDO


def test_numeracao_propria_e_lista_da_mais_recente(session, sessao):
    assert proximo_numero_versao_proposta(session, sessao.id) == 1
    _registrar(session, sessao.id, 1)
    _registrar(session, sessao.id, 2)
    assert proximo_numero_versao_proposta(session, sessao.id) == 3
    assert [v.numero for v in versoes_da_proposta(session, sessao.id)] == [2, 1]


def test_numero_repetido_e_recusado_e_a_sessao_continua_usavel(session, sessao):
    _registrar(session, sessao.id, 1)
    with pytest.raises(IntegrityError):
        _registrar(session, sessao.id, 1)
    _registrar(session, sessao.id, 2)


@pytest.mark.parametrize(
    ("campos", "erro"),
    [
        ({"numero": 0}, "numero"),
        ({"conteudo": " "}, "conteudo_md"),
        ({"pdf": b""}, "pdf"),
    ],
)
def test_valores_invalidos(session, sessao, campos, erro):
    with pytest.raises((ValueError, TypeError), match=erro):
        _registrar(session, sessao.id, **campos)


def test_clausulas_precisam_ter_id_titulo_e_texto(session, sessao):
    with pytest.raises(ValueError, match="clausulas"):
        registrar_versao_proposta(
            session,
            sessao.id,
            numero=1,
            emitido_em=EMITIDO,
            conteudo_md="x",
            pdf=b"x",
            versao_modelo=1,
            clausulas=[{"id": "foro"}],
        )


def test_recriar_a_proposta_mantem_as_versoes(session, sessao):
    _registrar(session, sessao.id)
    excluir_proposta(session, sessao.id)
    assert len(versoes_da_proposta(session, sessao.id)) == 1


def test_excluir_sessao_apaga_as_versoes(session, sessao):
    _registrar(session, sessao.id)
    excluir_sessao(session, sessao.id)
    assert session.exec(select(VersaoProposta)).all() == []

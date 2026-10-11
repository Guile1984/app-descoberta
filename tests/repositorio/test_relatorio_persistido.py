"""Hipóteses dos cálculos e versões do relatório registradas como enviadas."""

import hashlib
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from descoberta.repositorio import (
    HipoteseMetrica,
    RegistroNaoEncontrado,
    TipoVersao,
    VersaoRelatorio,
    criar_sessao,
    excluir_sessao,
    hipoteses_da_sessao,
    marcar_hipotese,
    obter_versao,
    proximo_numero_versao,
    registrar_versao,
    versoes_da_sessao,
)

EMITIDO = datetime(2026, 10, 11, 14, 5, tzinfo=UTC)

# --- Hipóteses ---


def test_marcar_e_desmarcar_hipotese(session, sessao):
    marcar_hipotese(session, sessao.id, "custo_hora", True)
    marcar_hipotese(session, sessao.id, "horas_economizadas_mes", True)
    marcar_hipotese(session, sessao.id, "custo_hora", True)  # de novo: não duplica
    assert hipoteses_da_sessao(session, sessao.id) == {"custo_hora", "horas_economizadas_mes"}
    assert len(session.exec(select(HipoteseMetrica)).all()) == 2

    marcar_hipotese(session, sessao.id, "custo_hora", False)
    marcar_hipotese(session, sessao.id, "investimento", False)  # não estava marcada: nada muda
    assert hipoteses_da_sessao(session, sessao.id) == {"horas_economizadas_mes"}


@pytest.mark.parametrize("campo", ["custo", "sessao_id", "frequencia_periodo"])
def test_so_metricas_numericas_podem_ser_hipotese(session, sessao, campo):
    with pytest.raises(ValueError, match="campo"):
        marcar_hipotese(session, sessao.id, campo, True)


def test_hipotese_em_sessao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        marcar_hipotese(session, 999, "custo_hora", True)


# --- Versões registradas ---


def _registrar(session, sessao_id, numero=1, tipo="cliente", conteudo="# Relatório", pdf=b"%PDF"):
    return registrar_versao(
        session,
        sessao_id,
        numero=numero,
        tipo=tipo,
        emitido_em=EMITIDO,
        conteudo_md=conteudo,
        pdf=pdf,
    )


def test_registrar_versao_guarda_pdf_e_os_dois_hashes(session, sessao):
    versao = _registrar(session, sessao.id, conteudo="# Relatório\n", pdf=b"%PDF-1.4 abc")
    session.expire_all()
    gravada = obter_versao(session, sessao.id, 1)
    assert gravada.id == versao.id
    assert gravada.tipo == TipoVersao.cliente
    assert gravada.pdf == b"%PDF-1.4 abc"
    assert gravada.conteudo_md == "# Relatório\n"
    # Hash do conteúdo: o que vai impresso no rodapé. Hash do PDF: confere o arquivo.
    assert gravada.hash_conteudo == hashlib.sha256("# Relatório\n".encode()).hexdigest()
    assert gravada.hash_pdf == hashlib.sha256(b"%PDF-1.4 abc").hexdigest()
    assert gravada.emitido_em.replace(tzinfo=UTC) == EMITIDO


def test_numeracao_das_versoes_por_sessao(session, sessao, cliente):
    assert proximo_numero_versao(session, sessao.id) == 1
    _registrar(session, sessao.id, numero=1)
    _registrar(session, sessao.id, numero=2, tipo="interna")
    assert proximo_numero_versao(session, sessao.id) == 3
    outra = criar_sessao(
        session, cliente_id=cliente.id, data=date(2026, 10, 8), versao_questionario=1
    )
    assert proximo_numero_versao(session, outra.id) == 1


def test_numero_repetido_e_recusado_pelo_banco(session, sessao):
    _registrar(session, sessao.id, numero=1)
    with pytest.raises(IntegrityError):
        _registrar(session, sessao.id, numero=1)


def test_lista_da_mais_recente_para_a_mais_antiga(session, sessao):
    for numero in (1, 2, 3):
        _registrar(session, sessao.id, numero=numero)
    assert [v.numero for v in versoes_da_sessao(session, sessao.id)] == [3, 2, 1]


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("tipo", "rascunho"), ("conteudo_md", "  "), ("pdf", b""), ("pdf", "texto"), ("numero", 0)],
)
def test_versao_invalida(session, sessao, campo, valor):
    dados = {"numero": 1, "tipo": "cliente", "conteudo": "# R", "pdf": b"%PDF"}
    dados[{"conteudo_md": "conteudo"}.get(campo, campo)] = valor
    with pytest.raises((ValueError, TypeError)):
        _registrar(session, sessao.id, **dados)
    assert versoes_da_sessao(session, sessao.id) == []


def test_versao_de_outra_sessao_nao_aparece(session, sessao):
    _registrar(session, sessao.id)
    assert obter_versao(session, sessao.id + 1, 1) is None


def test_excluir_a_sessao_apaga_hipoteses_e_versoes(session, sessao):
    marcar_hipotese(session, sessao.id, "custo_hora", True)
    _registrar(session, sessao.id)
    excluir_sessao(session, sessao.id)
    session.expire_all()
    assert session.exec(select(HipoteseMetrica)).all() == []
    assert session.exec(select(VersaoRelatorio)).all() == []

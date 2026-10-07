from decimal import Decimal

import pytest
from sqlalchemy import text

from descoberta.repositorio import obter_metricas, salvar_metricas
from descoberta.repositorio.tipos import DecimalTexto


@pytest.mark.parametrize("valor", ["0.10", "20000.00", "7.692307692307692307692307692", "0"])
def test_decimal_volta_identico(session, sessao, valor):
    salvar_metricas(session, sessao.id, custo_hora=Decimal(valor))
    session.expire_all()  # força a releitura do banco, em vez do objeto em memória
    lido = obter_metricas(session, sessao.id).custo_hora
    assert isinstance(lido, Decimal)
    assert str(lido) == valor


def test_decimal_gravado_como_texto(session, sessao):
    salvar_metricas(session, sessao.id, custo_hora=Decimal("0.10"))
    bruto = session.exec(text("SELECT custo_hora, typeof(custo_hora) FROM metricas")).one()
    assert tuple(bruto) == ("0.10", "text")


def test_none_volta_none(session, sessao):
    salvar_metricas(session, sessao.id, custo_hora=None)
    session.expire_all()
    assert obter_metricas(session, sessao.id).custo_hora is None


def test_tipo_recusa_float_direto():
    with pytest.raises(TypeError, match="Decimal"):
        DecimalTexto().process_bind_param(0.1, dialect=None)

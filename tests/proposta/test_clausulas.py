"""Cláusulas efetivas de uma proposta: o modelo com os ajustes e as exclusões dela."""

from pathlib import Path

import pytest

from descoberta.proposta import carregar_modelo_proposta
from descoberta.proposta.clausulas import (
    Ajuste,
    clausulas_efetivas,
    conferir_ajuste,
    marcadores_desconhecidos,
    preencher_marcadores,
)

MODELO = carregar_modelo_proposta(
    Path(__file__).resolve().parents[2] / "config" / "proposta_v1.yaml"
)


def test_sem_ajustes_valem_as_do_modelo():
    efetivas = clausulas_efetivas(MODELO, {})
    assert [c.id for c in efetivas] == [c.id for c in MODELO.clausulas]
    assert not any(c.ajustada for c in efetivas)


def test_texto_ajustado_substitui_o_do_modelo():
    efetivas = clausulas_efetivas(MODELO, {"suporte_garantia": Ajuste(texto="60 dias.")})
    suporte = next(c for c in efetivas if c.id == "suporte_garantia")
    assert (suporte.texto, suporte.ajustada) == ("60 dias.", True)
    assert suporte.titulo == MODELO.clausula("suporte_garantia").titulo


def test_clausula_excluida_sai():
    efetivas = clausulas_efetivas(MODELO, {"cancelamento": Ajuste(excluida=True)})
    assert "cancelamento" not in [c.id for c in efetivas]


def test_ajuste_de_clausula_que_saiu_do_modelo_e_ignorado():
    assert len(clausulas_efetivas(MODELO, {"antiga": Ajuste(texto="x")})) == len(MODELO.clausulas)


def test_nao_removivel_nao_pode_ser_excluida():
    with pytest.raises(ValueError, match="não pode ser excluída"):
        conferir_ajuste(MODELO, "foro", excluida=True)
    conferir_ajuste(MODELO, "cancelamento", excluida=True)


def test_ajuste_com_marcador_desconhecido():
    with pytest.raises(ValueError, match="cliente.cnpj"):
        conferir_ajuste(MODELO, "foro", texto="Foro de {cliente.cnpj}.")


def test_ajuste_de_clausula_inexistente():
    with pytest.raises(KeyError, match="xyz"):
        conferir_ajuste(MODELO, "xyz", texto="x")


def test_marcadores():
    assert marcadores_desconhecidos("{foro} e {cliente.empresa} e {outro}") == ["outro"]
    valores = {"foro": "São Paulo/SP", "cliente.empresa": "Construtora Alvorada"}
    assert preencher_marcadores("Foro de {foro}; cliente {cliente.empresa}.", valores, "?") == (
        "Foro de São Paulo/SP; cliente Construtora Alvorada."
    )


def test_marcador_sem_valor_fica_a_preencher():
    # A marca do que falta vem de quem monta o documento.
    assert preencher_marcadores("Foro de {foro}.", {"foro": None}, "[falta]") == "Foro de [falta]."

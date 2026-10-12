"""Proposta Comercial no banco: criação a partir do conteúdo inicial, edição e listas."""

from decimal import Decimal

import pytest
from sqlmodel import select

from descoberta.proposta.clausulas import Ajuste
from descoberta.proposta.inicial import FaseInicial, PropostaInicial
from descoberta.repositorio import (
    ClausulaProposta,
    FaseProposta,
    ItemProposta,
    Proposta,
    RegistroNaoEncontrado,
    TipoItemProposta,
    adicionar_item,
    ajustar_clausula,
    ajustes_das_clausulas,
    criar_proposta,
    editar_item,
    excluir_item,
    excluir_proposta,
    excluir_sessao,
    itens_da_sessao,
    obter_proposta,
    restaurar_clausula,
    salvar_proposta,
)

INICIAL = PropostaInicial(
    validade_dias=15,
    condicoes_pagamento="50% no aceite",
    impostos="Inclusos",
    reajuste="IPCA",
    fases=[
        FaseInicial("Fase 0", "Preparar os dados", 4, None, ["Rotular"], ["Base rotulada"]),
        FaseInicial("MVP", "Construir", 8, Decimal("20000"), ["Triagem"], ["MVP", "Manual"]),
    ],
    exclusoes=["Laudo automático"],
    premissas=["Prazos a partir do aceite"],
    responsabilidades=["Enviar a amostra"],
)


def _itens(session, sessao_id, tipo):
    return itens_da_sessao(session, ItemProposta, sessao_id, tipo=tipo)


def test_criar_proposta_grava_tudo(session, sessao):
    proposta = criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    assert proposta.versao_modelo == 1
    assert proposta.validade_dias == 15
    assert proposta.criada_com_alerta is False
    fase_0, mvp = itens_da_sessao(session, FaseProposta, sessao.id)
    assert (mvp.nome, mvp.duracao_semanas, mvp.investimento) == ("MVP", 8, Decimal("20000"))
    assert fase_0.investimento is None
    escopo = _itens(session, sessao.id, TipoItemProposta.escopo)
    assert [(i.texto, i.fase_id) for i in escopo] == [("Rotular", fase_0.id), ("Triagem", mvp.id)]
    entregaveis = _itens(session, sessao.id, TipoItemProposta.entregavel)
    assert [i.texto for i in entregaveis] == ["Base rotulada", "MVP", "Manual"]
    assert [i.texto for i in _itens(session, sessao.id, TipoItemProposta.exclusao)] == [
        "Laudo automático"
    ]
    assert _itens(session, sessao.id, TipoItemProposta.premissa)[0].fase_id is None
    assert len(_itens(session, sessao.id, TipoItemProposta.responsabilidade)) == 1


def test_proposta_criada_apesar_do_alerta(session, sessao):
    proposta = criar_proposta(session, sessao.id, INICIAL, versao_modelo=1, com_alerta=True)
    assert proposta.criada_com_alerta is True


def test_so_uma_proposta_por_sessao(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    with pytest.raises(ValueError, match="já tem proposta"):
        criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)


def test_proposta_em_sessao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        criar_proposta(session, 999, INICIAL, versao_modelo=1)


def test_salvar_campos_da_proposta(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    salvar_proposta(
        session,
        sessao.id,
        cliente_cpf_cnpj="11222333000181",
        cliente_representante="Roberto",
        cliente_cargo="Sócio-diretor",
        cliente_email="roberto@example.com",
        validade_dias=30,
        reajuste="  Sem reajuste  ",
    )
    proposta = obter_proposta(session, sessao.id)
    assert proposta.cliente_cpf_cnpj == "11.222.333/0001-81"
    assert proposta.validade_dias == 30
    assert proposta.reajuste == "Sem reajuste"


@pytest.mark.parametrize(
    ("campos", "erro"),
    [
        ({"cliente_cpf_cnpj": "123"}, "CPF"),
        ({"cliente_email": "sem-arroba"}, "e-mail"),
        ({"validade_dias": 0}, "validade_dias"),
        ({"condicoes_pagamento": "  "}, "condicoes_pagamento"),
        ({"versao_modelo": 2}, "campo desconhecido"),
    ],
)
def test_campos_invalidos(session, sessao, campos, erro):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    with pytest.raises(ValueError, match=erro):
        salvar_proposta(session, sessao.id, **campos)


def test_salvar_sem_proposta(session, sessao):
    with pytest.raises(RegistroNaoEncontrado, match="proposta"):
        salvar_proposta(session, sessao.id, validade_dias=10)


def test_listas_da_proposta(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    fase = adicionar_item(session, FaseProposta, sessao.id, nome="Sustentação", duracao_semanas=4)
    item = adicionar_item(
        session,
        ItemProposta,
        sessao.id,
        tipo=TipoItemProposta.escopo,
        texto="Ajustes do modelo",
        fase_id=fase.id,
    )
    editar_item(session, ItemProposta, item.id, texto="Ajustes finos")
    assert _itens(session, sessao.id, TipoItemProposta.escopo)[-1].texto == "Ajustes finos"
    excluir_item(session, ItemProposta, item.id)
    assert len(_itens(session, sessao.id, TipoItemProposta.escopo)) == 2


def test_item_nao_pode_apontar_para_fase_de_outra_sessao(session, sessao, outra_sessao):
    criar_proposta(session, outra_sessao.id, INICIAL, versao_modelo=1)
    fase_alheia = itens_da_sessao(session, FaseProposta, outra_sessao.id)[0]
    with pytest.raises(ValueError, match="fase"):
        adicionar_item(
            session,
            ItemProposta,
            sessao.id,
            tipo=TipoItemProposta.escopo,
            texto="X",
            fase_id=fase_alheia.id,
        )


def test_excluir_fase_leva_os_itens_dela(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    fase_0 = itens_da_sessao(session, FaseProposta, sessao.id)[0]
    excluir_item(session, FaseProposta, fase_0.id)
    session.expire_all()
    textos = [i.texto for i in itens_da_sessao(session, ItemProposta, sessao.id)]
    assert "Rotular" not in textos
    assert "Base rotulada" not in textos
    assert "Triagem" in textos


def test_fase_com_duracao_invalida(session, sessao):
    with pytest.raises(ValueError, match="duracao_semanas"):
        adicionar_item(session, FaseProposta, sessao.id, nome="X", duracao_semanas=0)


def test_excluir_proposta_apaga_fases_e_itens(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    excluir_proposta(session, sessao.id)
    assert obter_proposta(session, sessao.id) is None
    assert itens_da_sessao(session, FaseProposta, sessao.id) == []
    assert itens_da_sessao(session, ItemProposta, sessao.id) == []


def test_excluir_sessao_apaga_a_proposta(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    excluir_sessao(session, sessao.id)
    for modelo in (Proposta, FaseProposta, ItemProposta, ClausulaProposta):
        assert session.exec(select(modelo)).all() == []


# --- Ajustes das cláusulas (Condições Gerais) ---


def test_ajustar_texto_e_excluir_clausula(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    ajustar_clausula(session, sessao.id, "suporte_garantia", texto="  60 dias.  ")
    ajustar_clausula(session, sessao.id, "cancelamento", excluida=True)
    assert ajustes_das_clausulas(session, sessao.id) == {
        "suporte_garantia": Ajuste(texto="60 dias."),
        "cancelamento": Ajuste(excluida=True),
    }


def test_ajustar_de_novo_atualiza(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    ajustar_clausula(session, sessao.id, "cancelamento", texto="A")
    ajustar_clausula(session, sessao.id, "cancelamento", texto="B")
    ajustar_clausula(session, sessao.id, "cancelamento", excluida=True)
    assert ajustes_das_clausulas(session, sessao.id) == {
        "cancelamento": Ajuste(texto="B", excluida=True)
    }
    ajustar_clausula(session, sessao.id, "cancelamento", excluida=False)
    assert ajustes_das_clausulas(session, sessao.id) == {"cancelamento": Ajuste(texto="B")}


def test_restaurar_volta_ao_modelo(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    ajustar_clausula(session, sessao.id, "foro", texto="Outro foro.")
    restaurar_clausula(session, sessao.id, "foro")
    restaurar_clausula(session, sessao.id, "foro")  # sem ajuste: nada a fazer
    assert ajustes_das_clausulas(session, sessao.id) == {}


@pytest.mark.parametrize(
    ("campos", "erro"),
    [({"texto": "   "}, "texto"), ({"texto": 3}, "texto"), ({"excluida": "sim"}, "excluida")],
)
def test_ajuste_invalido(session, sessao, campos, erro):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    with pytest.raises((ValueError, TypeError), match=erro):
        ajustar_clausula(session, sessao.id, "foro", **campos)


def test_ajuste_exige_proposta(session, sessao):
    with pytest.raises(RegistroNaoEncontrado, match="proposta"):
        ajustar_clausula(session, sessao.id, "foro", texto="X")


def test_recriar_a_proposta_apaga_os_ajustes(session, sessao):
    criar_proposta(session, sessao.id, INICIAL, versao_modelo=1)
    ajustar_clausula(session, sessao.id, "foro", texto="X")
    excluir_proposta(session, sessao.id)
    assert ajustes_das_clausulas(session, sessao.id) == {}

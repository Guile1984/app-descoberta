"""Saídas da revisão pós-sessão: riscos, indicadores, escopo, próximos passos e textos."""

import sqlite3
from datetime import date

import pytest
from sqlmodel import Session, select

from descoberta.dominio.revisao import Camada, Nivel, Responsavel
from descoberta.repositorio import (
    Indicador,
    ItemEscopo,
    ProximoPasso,
    RegistroNaoEncontrado,
    Risco,
    TextoSecao,
    adicionar_item,
    criar_engine,
    criar_sessao,
    criar_tabelas,
    editar_item,
    excluir_item,
    excluir_sessao,
    itens_da_sessao,
    listar_clientes,
    salvar_texto_secao,
    textos_da_sessao,
)

RISCO = {
    "descricao": "Fotos mostram o interior das casas",
    "categoria": "lgpd",
    "probabilidade": "alto",
    "impacto": "alto",
    "mitigacao": "Recortar a área da fissura",
}

# --- Riscos ---


def test_adicionar_risco(session, sessao):
    risco = adicionar_item(session, Risco, sessao.id, **RISCO)
    session.expire_all()
    [gravado] = itens_da_sessao(session, Risco, sessao.id)
    assert gravado.id == risco.id
    assert gravado.categoria == "lgpd"
    assert (gravado.probabilidade, gravado.impacto) == (Nivel.alto, Nivel.alto)
    assert gravado.mitigacao == "Recortar a área da fissura"


def test_mitigacao_e_opcional(session, sessao):
    risco = adicionar_item(session, Risco, sessao.id, **(RISCO | {"mitigacao": "  "}))
    assert risco.mitigacao is None


@pytest.mark.parametrize("campo", ["descricao", "categoria", "probabilidade", "impacto"])
def test_campos_obrigatorios_do_risco(session, sessao, campo):
    campos = dict(RISCO)
    del campos[campo]
    with pytest.raises(ValueError, match=campo):
        adicionar_item(session, Risco, sessao.id, **campos)


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("descricao", "   "),
        ("categoria", "LGPD"),  # rótulo em vez do id do YAML
        ("probabilidade", "altissimo"),
        ("impacto", ""),
    ],
)
def test_valores_invalidos_do_risco(session, sessao, campo, valor):
    with pytest.raises(ValueError, match=campo):
        adicionar_item(session, Risco, sessao.id, **(RISCO | {campo: valor}))
    assert itens_da_sessao(session, Risco, sessao.id) == []


def test_campo_desconhecido_e_recusado(session, sessao):
    with pytest.raises(ValueError, match="desconhecido"):
        adicionar_item(session, Risco, sessao.id, **RISCO, gravidade="alta")


def test_sessao_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        adicionar_item(session, Risco, 999, **RISCO)


def test_editar_risco(session, sessao):
    risco = adicionar_item(session, Risco, sessao.id, **RISCO)
    editar_item(session, Risco, risco.id, impacto="medio", mitigacao="")
    session.expire_all()
    [gravado] = itens_da_sessao(session, Risco, sessao.id)
    assert gravado.impacto == Nivel.medio
    assert gravado.mitigacao is None
    assert gravado.descricao == RISCO["descricao"]  # o resto não muda


def test_edicao_invalida_nao_grava_nada(session, sessao):
    risco = adicionar_item(session, Risco, sessao.id, **RISCO)
    with pytest.raises(ValueError, match="probabilidade"):
        editar_item(session, Risco, risco.id, impacto="medio", probabilidade="x")
    session.expire_all()
    assert itens_da_sessao(session, Risco, sessao.id)[0].impacto == Nivel.alto


def test_excluir_risco(session, sessao):
    risco = adicionar_item(session, Risco, sessao.id, **RISCO)
    excluir_item(session, Risco, risco.id)
    assert itens_da_sessao(session, Risco, sessao.id) == []
    with pytest.raises(RegistroNaoEncontrado):
        excluir_item(session, Risco, risco.id)
    with pytest.raises(RegistroNaoEncontrado):
        editar_item(session, Risco, risco.id, impacto="baixo")


def test_itens_na_ordem_em_que_foram_criados(session, sessao):
    for descricao in ("Primeiro", "Segundo", "Terceiro"):
        adicionar_item(session, Risco, sessao.id, **(RISCO | {"descricao": descricao}))
    nomes = [r.descricao for r in itens_da_sessao(session, Risco, sessao.id)]
    assert nomes == ["Primeiro", "Segundo", "Terceiro"]


# --- Indicadores, escopo e próximos passos ---


def test_indicador(session, sessao):
    indicador = adicionar_item(
        session,
        Indicador,
        sessao.id,
        nome="Recall de fissuras graves",
        camada="tecnica",
        valor_atual="Não medido",
        meta="≥ 95%",
        prazo="Fim do piloto",
        como_medir="40 casos graves com laudo",
    )
    assert indicador.camada == Camada.tecnica
    assert indicador.meta == "≥ 95%"  # texto: não entra em cálculo


def test_indicador_so_com_nome_e_camada(session, sessao):
    indicador = adicionar_item(session, Indicador, sessao.id, nome="Horas", camada="negocio")
    assert indicador.valor_atual is indicador.meta is indicador.prazo is None


def test_camada_invalida(session, sessao):
    with pytest.raises(ValueError, match="camada"):
        adicionar_item(session, Indicador, sessao.id, nome="Horas", camada="financeira")


def test_item_de_escopo(session, sessao):
    adicionar_item(session, ItemEscopo, sessao.id, texto="Triagem por foto", entra=True)
    adicionar_item(session, ItemEscopo, sessao.id, texto="Laudo automático", entra=False)
    itens = itens_da_sessao(session, ItemEscopo, sessao.id)
    assert [(i.texto, i.entra) for i in itens] == [
        ("Triagem por foto", True),
        ("Laudo automático", False),
    ]


def test_entra_precisa_ser_sim_ou_nao(session, sessao):
    with pytest.raises(TypeError):
        adicionar_item(session, ItemEscopo, sessao.id, texto="Triagem", entra="sim")


def test_proximo_passo(session, sessao):
    passo = adicionar_item(
        session,
        ProximoPasso,
        sessao.id,
        acao="Enviar os 40 casos graves",
        responsavel="cliente",
        prazo=date(2026, 10, 14),
    )
    session.expire_all()
    [gravado] = itens_da_sessao(session, ProximoPasso, sessao.id)
    assert gravado.id == passo.id
    assert gravado.responsavel == Responsavel.cliente
    assert gravado.prazo == date(2026, 10, 14)


def test_prazo_do_passo_e_opcional_mas_precisa_ser_data(session, sessao):
    passo = adicionar_item(
        session, ProximoPasso, sessao.id, acao="Validar critério", responsavel="consultor"
    )
    assert passo.prazo is None
    with pytest.raises(TypeError):
        editar_item(session, ProximoPasso, passo.id, prazo="14/10/2026")


def test_listas_sao_separadas_por_sessao(session, sessao, cliente):
    outra = criar_sessao(
        session, cliente_id=cliente.id, data=date(2026, 10, 8), versao_questionario=1
    )
    adicionar_item(session, Risco, sessao.id, **RISCO)
    assert itens_da_sessao(session, Risco, outra.id) == []


# --- Textos das seções ---


def test_salvar_texto_de_secao(session, sessao):
    salvar_texto_secao(session, sessao.id, "frase_problema", "Hoje o Marcos gasta 60 h/mês…")
    salvar_texto_secao(session, sessao.id, "frase_problema", "Versão final")
    assert textos_da_sessao(session, sessao.id) == {"frase_problema": "Versão final"}
    assert len(session.exec(select(TextoSecao)).all()) == 1


def test_texto_vazio_apaga(session, sessao):
    salvar_texto_secao(session, sessao.id, "recomendacao", "Seguir com fase 0")
    assert salvar_texto_secao(session, sessao.id, "recomendacao", "  ") is None
    assert textos_da_sessao(session, sessao.id) == {}


def test_texto_precisa_ser_texto(session, sessao):
    with pytest.raises(TypeError):
        salvar_texto_secao(session, sessao.id, "recomendacao", None)


def test_id_de_secao_invalido(session, sessao):
    with pytest.raises(ValueError, match="secao_id"):
        salvar_texto_secao(session, sessao.id, "Frase Problema", "texto")


# --- Exclusão em cascata e bancos antigos ---


def test_excluir_a_sessao_apaga_as_saidas(session, sessao):
    adicionar_item(session, Risco, sessao.id, **RISCO)
    adicionar_item(session, Indicador, sessao.id, nome="Horas", camada="negocio")
    adicionar_item(session, ItemEscopo, sessao.id, texto="Triagem", entra=True)
    adicionar_item(session, ProximoPasso, sessao.id, acao="Amostra", responsavel="cliente")
    salvar_texto_secao(session, sessao.id, "recomendacao", "Seguir com fase 0")
    excluir_sessao(session, sessao.id)
    session.expire_all()
    for modelo in (Risco, Indicador, ItemEscopo, ProximoPasso, TextoSecao):
        assert session.exec(select(modelo)).all() == []


def test_banco_antigo_ganha_as_tabelas_novas_sem_perder_dados(tmp_path):
    caminho = tmp_path / "antigo.db"
    # Banco como estava no Sprint 5: só um cliente, sem as tabelas da revisão.
    with sqlite3.connect(caminho) as conexao:
        conexao.execute(
            "CREATE TABLE cliente (id INTEGER PRIMARY KEY, nome VARCHAR NOT NULL, "
            "empresa VARCHAR NOT NULL, setor VARCHAR, num_funcionarios INTEGER, "
            "contato VARCHAR, criado_em DATETIME NOT NULL)"
        )
        conexao.execute(
            "INSERT INTO cliente (nome, empresa, criado_em) "
            "VALUES ('Roberto', 'Alvorada', '2026-10-07 12:00:00')"
        )
    conexao.close()

    engine = criar_engine(caminho)
    criar_tabelas(engine)
    with Session(engine) as session:
        [cliente] = listar_clientes(session)
        sessao = criar_sessao(
            session, cliente_id=cliente.id, data=date(2026, 10, 7), versao_questionario=1
        )
        adicionar_item(session, Risco, sessao.id, **RISCO)
        assert len(itens_da_sessao(session, Risco, sessao.id)) == 1
    engine.dispose()

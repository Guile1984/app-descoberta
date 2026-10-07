import pytest
from sqlmodel import select

from descoberta.repositorio import (
    Metricas,
    RegistroNaoEncontrado,
    Resposta,
    Sessao,
    atualizar_cliente,
    criar_cliente,
    excluir_cliente,
    listar_clientes,
    marcar_sinal,
    obter_cliente,
    salvar_metricas,
    salvar_resposta,
)


def test_criar_e_obter(session, cliente):
    lido = obter_cliente(session, cliente.id)
    assert lido.nome == "Roberto"
    assert lido.empresa == "Construtora Alvorada"
    assert lido.setor == "Construção civil"
    assert lido.num_funcionarios == 40
    assert lido.contato == "roberto@alvorada.example"
    assert lido.criado_em is not None


def test_campos_opcionais(session):
    cliente = criar_cliente(session, nome="Ana", empresa="Padaria Sol")
    assert cliente.setor is None
    assert cliente.num_funcionarios is None
    assert cliente.contato is None


def test_obter_inexistente_devolve_none(session):
    assert obter_cliente(session, 999) is None


def test_listar_ordenado_por_empresa(session):
    criar_cliente(session, nome="Ana", empresa="Padaria Sol")
    criar_cliente(session, nome="Roberto", empresa="Construtora Alvorada")
    assert [c.empresa for c in listar_clientes(session)] == [
        "Construtora Alvorada",
        "Padaria Sol",
    ]


def test_atualizar(session, cliente):
    atualizar_cliente(session, cliente.id, setor="Engenharia", num_funcionarios=45)
    lido = obter_cliente(session, cliente.id)
    assert lido.setor == "Engenharia"
    assert lido.num_funcionarios == 45
    assert lido.nome == "Roberto"  # campos não informados ficam como estavam


def test_atualizar_campo_desconhecido(session, cliente):
    with pytest.raises(ValueError, match="campo desconhecido 'telefone'"):
        atualizar_cliente(session, cliente.id, telefone="123")


def test_atualizar_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado, match="cliente 999"):
        atualizar_cliente(session, 999, nome="X")


@pytest.mark.parametrize(
    ("campos", "erro"),
    [
        ({"nome": "", "empresa": "X"}, "nome"),
        ({"nome": "   ", "empresa": "X"}, "nome"),
        ({"nome": "X", "empresa": ""}, "empresa"),
        ({"nome": "X", "empresa": "Y", "num_funcionarios": -1}, "num_funcionarios"),
    ],
)
def test_valores_invalidos(session, campos, erro):
    with pytest.raises(ValueError, match=erro):
        criar_cliente(session, **campos)


@pytest.mark.parametrize("valor", ["40", 4.0, True])
def test_num_funcionarios_precisa_ser_inteiro(session, valor):
    with pytest.raises(TypeError, match="num_funcionarios"):
        criar_cliente(session, nome="X", empresa="Y", num_funcionarios=valor)


def test_texto_e_aparado(session):
    cliente = criar_cliente(session, nome="  Ana  ", empresa=" Padaria Sol ", setor="  ")
    assert cliente.nome == "Ana"
    assert cliente.empresa == "Padaria Sol"
    assert cliente.setor is None  # texto opcional em branco vira "sem valor"


def test_excluir_apaga_sessoes_e_registros_em_cascata(session, cliente, sessao):
    salvar_resposta(session, sessao.id, "b1.o1", "Orçamentos demoram.")
    marcar_sinal(session, sessao.id, "b1.s4")
    salvar_metricas(session, sessao.id, investimento=20_000)

    excluir_cliente(session, cliente.id)

    assert obter_cliente(session, cliente.id) is None
    assert session.exec(select(Sessao)).all() == []
    assert session.exec(select(Resposta)).all() == []
    assert session.exec(select(Metricas)).all() == []


def test_excluir_inexistente(session):
    with pytest.raises(RegistroNaoEncontrado):
        excluir_cliente(session, 999)


@pytest.mark.parametrize(("campos", "erro"), [({"nome": 123}, "nome"), ({"setor": 5}, "setor")])
def test_texto_precisa_ser_texto(session, campos, erro):
    with pytest.raises(TypeError, match=erro):
        criar_cliente(session, **({"nome": "X", "empresa": "Y"} | campos))

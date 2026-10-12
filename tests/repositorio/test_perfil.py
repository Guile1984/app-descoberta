"""Perfil do consultor: uma linha só, usada em todos os documentos."""

import io

import pytest
from PIL import Image
from sqlmodel import select

from descoberta.repositorio import (
    PerfilConsultor,
    obter_perfil,
    remover_logotipo,
    salvar_logotipo,
    salvar_perfil,
)


def _png() -> bytes:
    saida = io.BytesIO()
    Image.new("RGB", (40, 20), "navy").save(saida, "PNG")
    return saida.getvalue()


def test_sem_perfil_devolve_none(session):
    assert obter_perfil(session) is None


def test_criar_perfil_completo(session):
    perfil = salvar_perfil(
        session,
        nome=" Ana Exemplo ",
        empresa="Exemplo Consultoria em IA Ltda",
        cpf_cnpj="11222333000181",
        email="ana@example.com",
        telefone="(11) 90000-0000",
        cidade="São Paulo",
        uf="sp",
    )
    assert perfil.nome == "Ana Exemplo"
    assert perfil.cpf_cnpj == "11.222.333/0001-81"  # guardado já formatado
    assert perfil.uf == "SP"
    assert perfil.dados_ficticios is False
    assert obter_perfil(session).empresa == "Exemplo Consultoria em IA Ltda"


def test_atualizacao_parcial_mantem_o_resto(session):
    salvar_perfil(session, nome="Ana", empresa="Exemplo", cidade="Campinas", uf="SP")
    salvar_perfil(session, telefone="(19) 3000-0000")
    perfil = obter_perfil(session)
    assert (perfil.nome, perfil.cidade, perfil.telefone) == ("Ana", "Campinas", "(19) 3000-0000")
    assert len(session.exec(select(PerfilConsultor)).all()) == 1


def test_campo_em_branco_apaga(session):
    salvar_perfil(session, nome="Ana", empresa="Exemplo", telefone="123")
    assert salvar_perfil(session, telefone="  ").telefone is None


@pytest.mark.parametrize(
    ("campos", "erro"),
    [
        ({"empresa": "Exemplo"}, "nome"),
        ({"nome": "Ana"}, "empresa"),
        ({"nome": " ", "empresa": "Exemplo"}, "nome"),
        ({"nome": "Ana", "empresa": "X", "cpf_cnpj": "111.444.777-36"}, "dígito verificador"),
        ({"nome": "Ana", "empresa": "X", "email": "ana-sem-arroba"}, "e-mail"),
        ({"nome": "Ana", "empresa": "X", "uf": "XX"}, "UF"),
        ({"nome": "Ana", "empresa": "X", "apelido": "A"}, "campo desconhecido"),
    ],
)
def test_valores_invalidos(session, campos, erro):
    with pytest.raises(ValueError, match=erro):
        salvar_perfil(session, **campos)
    assert obter_perfil(session) is None


def test_nome_nao_pode_ser_apagado_depois(session):
    salvar_perfil(session, nome="Ana", empresa="Exemplo")
    with pytest.raises(ValueError, match="nome"):
        salvar_perfil(session, nome="")
    assert obter_perfil(session).nome == "Ana"


def test_logotipo_e_regravado_e_pode_ser_removido(session):
    salvar_perfil(session, nome="Ana", empresa="Exemplo")
    perfil = salvar_logotipo(session, _png())
    assert perfil.logotipo.startswith(b"\x89PNG")
    assert remover_logotipo(session).logotipo is None


def test_logotipo_invalido_nao_grava(session):
    salvar_perfil(session, nome="Ana", empresa="Exemplo")
    with pytest.raises(ValueError, match="PNG ou JPEG"):
        salvar_logotipo(session, b"texto")
    assert obter_perfil(session).logotipo is None


def test_logotipo_exige_perfil(session):
    with pytest.raises(ValueError, match="perfil"):
        salvar_logotipo(session, _png())


def test_marca_de_dados_ficticios(session):
    perfil = salvar_perfil(session, nome="Ana", empresa="Exemplo", dados_ficticios=True)
    assert perfil.dados_ficticios is True

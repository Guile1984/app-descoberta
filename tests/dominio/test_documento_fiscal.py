"""CPF e CNPJ: dígitos verificadores e formatação."""

import pytest

from descoberta.dominio.documento_fiscal import formatar_cpf_cnpj


@pytest.mark.parametrize(
    ("digitado", "formatado"),
    [
        ("111.444.777-35", "111.444.777-35"),
        ("11144477735", "111.444.777-35"),
        (" 111 444 777 35 ", "111.444.777-35"),
        ("11.222.333/0001-81", "11.222.333/0001-81"),
        ("11222333000181", "11.222.333/0001-81"),
        # CNPJ alfanumérico (em vigor desde julho de 2026): letras nas 12 primeiras posições.
        ("12.ABC.345/01DE-35", "12.ABC.345/01DE-35"),
        ("12abc34501de35", "12.ABC.345/01DE-35"),
    ],
)
def test_documentos_validos(digitado, formatado):
    assert formatar_cpf_cnpj(digitado) == formatado


@pytest.mark.parametrize(
    ("digitado", "erro"),
    [
        ("111.444.777-36", "dígito verificador"),
        ("11.222.333/0001-82", "dígito verificador"),
        ("12.ABC.345/01DE-36", "dígito verificador"),
        ("000.000.000-00", "dígito verificador"),  # repetidos passam na conta, mas não existem
        ("11.111.111/1111-11", "dígito verificador"),
        ("1234567890", "11 dígitos"),
        ("123456789012345", "11 dígitos"),
        ("111.444.777-3A", "11 dígitos"),  # letra no CPF
        ("12.ABC.345/01DE-3X", "dígitos verificadores do CNPJ são números"),
        ("111#444#777#35", "11 dígitos"),
    ],
)
def test_documentos_invalidos(digitado, erro):
    with pytest.raises(ValueError, match=erro):
        formatar_cpf_cnpj(digitado)

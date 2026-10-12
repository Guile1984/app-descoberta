"""CPF e CNPJ: conferência dos dígitos verificadores, que pega erros de digitação.

A conta não diz se o documento existe; diz só se os números combinam entre si.

CNPJ alfanumérico (Receita Federal, em vigor desde julho de 2026): as 12 primeiras
posições podem ter letras; os 2 dígitos verificadores continuam números. Na conta, cada
caractere vale o seu código ASCII menos 48: "0"…"9" valem 0…9, "A" vale 17, "B" 18 etc.
Para CNPJs só com números, a conta é a mesma de sempre.
"""

import re

_PESOS_CPF_1 = range(10, 1, -1)  # 10, 9, …, 2
_PESOS_CPF_2 = range(11, 1, -1)
_PESOS_CNPJ_1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_PESOS_CNPJ_2 = (6, *_PESOS_CNPJ_1)

_SEPARADORES = re.compile(r"[\s./-]")


def _valor(caractere: str) -> int:
    return ord(caractere) - 48


def _digito_cpf(base: str, pesos: range) -> str:
    resto = sum(_valor(c) * p for c, p in zip(base, pesos, strict=True)) * 10 % 11
    return str(0 if resto == 10 else resto)


def _digito_cnpj(base: str, pesos: tuple[int, ...]) -> str:
    resto = sum(_valor(c) * p for c, p in zip(base, pesos, strict=True)) % 11
    return str(0 if resto < 2 else 11 - resto)


def _cpf(numeros: str) -> str:
    esperado = _digito_cpf(numeros[:9], _PESOS_CPF_1)
    esperado += _digito_cpf(numeros[:9] + esperado, _PESOS_CPF_2)
    if numeros[9:] != esperado or len(set(numeros)) == 1:
        raise ValueError("CPF com dígito verificador errado; confira a digitação")
    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"


def _cnpj(caracteres: str) -> str:
    if not caracteres[12:].isdigit():
        raise ValueError("os dois dígitos verificadores do CNPJ são números")
    esperado = _digito_cnpj(caracteres[:12], _PESOS_CNPJ_1)
    esperado += _digito_cnpj(caracteres[:12] + esperado, _PESOS_CNPJ_2)
    if caracteres[12:] != esperado or len(set(caracteres)) == 1:
        raise ValueError("CNPJ com dígito verificador errado; confira a digitação")
    c = caracteres
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"


def formatar_cpf_cnpj(texto: str) -> str:
    """CPF (11 dígitos) ou CNPJ (14 caracteres) conferido e no formato padrão.

    Aceita com ou sem pontuação. ValueError com a explicação quando não confere.
    """
    caracteres = _SEPARADORES.sub("", texto).upper()
    if len(caracteres) == 11 and caracteres.isdigit():
        return _cpf(caracteres)
    if len(caracteres) == 14 and caracteres.isascii() and caracteres.isalnum():
        return _cnpj(caracteres)
    raise ValueError("use um CPF (11 dígitos) ou um CNPJ (14 caracteres), com ou sem pontuação")

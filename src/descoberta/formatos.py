"""Números no formato brasileiro, usados pela web e pelo relatório.

Vírgula para decimais, ponto para separar milhares.

Ler: "20.000", "20000", "7,5", "3.000,50" e "R$ 400" são aceitos. "7.5" é recusado: no
Brasil o ponto separa milhares, e ler "7.5" como 75 (ou como 7,5) sem avisar seria pior
do que pedir a vírgula.

Mostrar: `moeda` (R$ 20.000,00), `numero` (7,7) e `numero_campo` (o valor dentro do
campo, que lido de novo dá exatamente o mesmo número).
"""

import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal

_COM_MILHAR = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?")
_SEM_MILHAR = re.compile(r"\d+(?:,\d+)?")
_PONTO_DECIMAL = re.compile(r"\d+\.\d+")


def ler_decimal(rotulo: str, texto: str) -> Decimal | None:
    """Texto do campo → Decimal; campo em branco → None (sem valor)."""
    texto = texto.strip().removeprefix("R$").strip()
    if not texto:
        return None
    if _COM_MILHAR.fullmatch(texto) or _SEM_MILHAR.fullmatch(texto):
        return Decimal(texto.replace(".", "").replace(",", "."))
    if _PONTO_DECIMAL.fullmatch(texto):
        raise ValueError(f"{rotulo}: use vírgula para decimais (ex.: 7,5), recebido '{texto}'")
    raise ValueError(f"{rotulo} precisa ser um número, como 7,5 ou 20.000 (recebido '{texto}')")


def _brasileiro(texto_en: str) -> str:
    # "20,000.50" (formato do Python) → "20.000,50"
    return texto_en.replace(",", "_").replace(".", ",").replace("_", ".")


def moeda(valor: Decimal) -> str:
    arredondado = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return "R$ " + _brasileiro(f"{arredondado:,.2f}")


def numero(valor: Decimal, casas: int = 1) -> str:
    """Arredonda para `casas` decimais e tira os zeros finais (60,0 → 60)."""
    arredondado = valor.quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)
    texto = _brasileiro(f"{arredondado:,.{casas}f}")
    if "," in texto:
        texto = texto.rstrip("0").rstrip(",")
    return texto


def numero_campo(valor: Decimal | None) -> str:
    """Valor para colocar dentro do campo, sem arredondar nada."""
    if valor is None:
        return ""
    casas = max(0, -valor.normalize().as_tuple().exponent)
    return numero(valor, casas)


def slug(texto: str) -> str:
    """Texto para nome de arquivo, só ASCII: "Construtora Alvorada" → "construtora-alvorada"."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-") or "cliente"

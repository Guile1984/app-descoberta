"""Contas da Proposta Comercial: cronograma, investimento total, validade e avisos.

O cronograma é em semanas contadas a partir do aceite (e não em datas): a proposta não
sabe quando o cliente vai aceitar. As fases são feitas uma depois da outra.

Os avisos (item repetido em mais de uma fase, total diferente do investimento da métrica)
só alertam o consultor: nada é mudado na proposta.
"""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class Periodo:
    inicio: int  # semana de início (a semana 1 começa no aceite)
    fim: int

    def __str__(self) -> str:
        if self.inicio == self.fim:
            return f"semana {self.inicio}"
        return f"semanas {self.inicio} a {self.fim}"


def cronograma(duracoes: Sequence[int | None]) -> list[Periodo | None]:
    """Período de cada fase, em sequência. Depois de uma fase sem duração, as seguintes
    ficam sem período (None): não dá para saber quando começam."""
    periodos: list[Periodo | None] = []
    proxima = 1
    for duracao in duracoes:
        if duracao is not None and duracao < 1:
            raise ValueError(f"duração de fase inválida: {duracao} semana(s)")
        if duracao is None or proxima is None:
            periodos.append(None)
            proxima = None
            continue
        periodos.append(Periodo(proxima, proxima + duracao - 1))
        proxima += duracao
    return periodos


def investimento_total(valores: Sequence[Decimal | None]) -> Decimal | None:
    """Soma das fases; sem total (None) se alguma fase ainda não tem valor."""
    if not valores or any(valor is None for valor in valores):
        return None
    return sum(valores, Decimal(0))


def valida_ate(emissao: date, dias: int) -> date:
    """Último dia de validade: a emissão mais `dias` dias corridos."""
    return emissao + timedelta(days=dias)


def diferenca_do_investimento(
    total: Decimal | None, investimento_da_metrica: Decimal | None
) -> Decimal | None:
    """Total da proposta menos o investimento da métrica (o do payback do relatório).

    None quando não há o que avisar: valores iguais, ou um dos dois ainda sem valor.
    """
    if total is None or investimento_da_metrica is None or total == investimento_da_metrica:
        return None
    return total - investimento_da_metrica


# --- Itens repetidos entre fases ---
#
# Comparação por palavras, sem LLM: dois itens de fases diferentes "se repetem" quando
# têm as mesmas palavras ou dividem pelo menos 3 palavras, que são no mínimo metade das
# palavras do item menor. Pega o mesmo item escrito de outro jeito ("Organização e
# rotulagem das fotos…" × "Organização e rotulagem do histórico…"), mas não sinônimos
# ("captura de fotos" × "coleta de dados"): é um alerta, a decisão é do consultor.

_COMUNS = (
    "a ao aos as com da das de do dos e em na nas no nos o os ou para pela pelas pelo "
    "pelos por que sem um uma umas uns cerca"
)
_PALAVRAS_COMUNS = frozenset(_COMUNS.split())
_PALAVRA = re.compile(r"\w+")
_MINIMO_EM_COMUM = 3


@dataclass(frozen=True)
class ItemRepetido:
    fase: str
    item: str
    outra_fase: str
    outro_item: str


def _raizes(texto: str) -> frozenset[str]:
    """Palavras do item sem acento, maiúsculas, plural e palavras comuns; cada uma
    reduzida às 5 primeiras letras (rotulagem/rotular → "rotul")."""
    sem_acento = unicodedata.normalize("NFKD", texto.casefold())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    raizes = set()
    for palavra in _PALAVRA.findall(sem_acento):
        if palavra in _PALAVRAS_COMUNS or (len(palavra) < 3 and not palavra.isdigit()):
            continue
        if len(palavra) > 3 and palavra.endswith("s"):
            palavra = palavra[:-1]
        raizes.add(palavra[:5])
    return frozenset(raizes)


def _se_repetem(a: frozenset[str], b: frozenset[str]) -> bool:
    if not a or not b:
        return False
    em_comum = len(a & b)
    return a == b or (em_comum >= _MINIMO_EM_COMUM and 2 * em_comum >= min(len(a), len(b)))


def itens_repetidos(fases: Sequence[tuple[str, Sequence[str]]]) -> list[ItemRepetido]:
    """Pares de itens de fases diferentes que parecem o mesmo item.

    `fases`: (nome da fase, itens de escopo), na ordem da proposta.
    """
    itens = [(nome, texto, _raizes(texto)) for nome, textos in fases for texto in textos]
    indice_da_fase = [i for i, (_, textos) in enumerate(fases) for _ in textos]
    repetidos = []
    for i, (fase, texto, raizes) in enumerate(itens):
        for j in range(i + 1, len(itens)):
            outra_fase, outro_texto, outras_raizes = itens[j]
            if indice_da_fase[i] != indice_da_fase[j] and _se_repetem(raizes, outras_raizes):
                repetidos.append(ItemRepetido(fase, texto, outra_fase, outro_texto))
    return repetidos

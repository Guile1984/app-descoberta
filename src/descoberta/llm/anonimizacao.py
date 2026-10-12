"""Anonimização: dados pessoais viram marcadores antes do LLM e voltam só na resposta.

Duas fontes:
- dados conhecidos da sessão (`Conhecido`): cliente, empresa, consultor, pessoas citadas,
  cidade… Para pessoas, cada parte do nome também é trocada ("Marcos Pereira" e "o
  Marcos"); para empresas, as partes que não são genéricas ("Alvorada", não "Construtora").
  As partes só são trocadas com maiúscula inicial: "Rosa" é nome, "rosa" é cor;
- formatos reconhecíveis: CPF, CNPJ (inclusive o alfanumérico), e-mail, telefone, CEP e
  endereço (Rua/Av./Rodovia… seguido do nome).

Cada valor tem um marcador estável ([CLIENTE], [PESSOA_1], [EMAIL_1]…), e o mesmo
`Anonimizador` usa sempre o mesmo marcador para o mesmo valor. `desfazer` troca os
marcadores de volta, localmente, e avisa os que a resposta inventou. `restantes` é a
conferência final: o que ainda parece dado pessoal num texto que vai sair.

Sem LLM e sem internet: regras fixas. Nomes que não são conhecidos e não têm formato
reconhecível (uma pessoa citada de passagem) só são pegos se estiverem na lista de pessoas
citadas da sessão; `sugerir_nomes` ajuda o consultor a montar essa lista.
"""

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

# Papéis com um valor só: o marcador não leva número ([CLIENTE], não [CLIENTE_1]).
PAPEIS_UNICOS = ("CLIENTE", "EMPRESA", "CONSULTOR", "EMPRESA_CONSULTOR", "REPRESENTANTE")

_CONECTORES = {"da", "das", "de", "do", "dos", "e"}
# Palavras de nomes de empresa que não identificam ninguém sozinhas.
_GENERICAS_DE_EMPRESA = {
    "assessoria",
    "associados",
    "cia",
    "comercio",
    "companhia",
    "construcoes",
    "construtora",
    "consultoria",
    "eireli",
    "empresa",
    "engenharia",
    "epp",
    "grupo",
    "industria",
    "ltda",
    "servicos",
    "solucoes",
    "tecnologia",
}

_VARIANTES = {
    "a": "aáàâãä",
    "e": "eéèêë",
    "i": "iíìîï",
    "o": "oóòôõö",
    "u": "uúùûü",
    "c": "cç",
    "n": "nñ",
}


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def _classe(letra: str, so_maiuscula: bool = False) -> str:
    base = _sem_acento(letra).lower()
    variantes = _VARIANTES.get(base, base)
    if so_maiuscula:
        return "[" + re.escape(variantes.upper()) + "]"
    return "[" + re.escape(variantes + variantes.upper()) + "]"


def _padrao_flexivel(valor: str, maiuscula_inicial: bool = False) -> str:
    """Casa o valor sem ligar para acentos, maiúsculas nem espaços repetidos.

    Com `maiuscula_inicial`, a primeira letra precisa ser maiúscula (partes de nome).
    """
    partes = []
    for i, caractere in enumerate(valor):
        if caractere.isspace():
            if not partes or partes[-1] != r"\s+":
                partes.append(r"\s+")
        elif caractere.isalpha():
            partes.append(_classe(caractere, so_maiuscula=maiuscula_inicial and i == 0))
        else:
            partes.append(re.escape(caractere))
    return r"(?<!\w)" + "".join(partes) + r"(?!\w)"


@dataclass(frozen=True)
class Conhecido:
    """Um dado pessoal que a sessão conhece, com o papel que vira o marcador."""

    valor: str
    papel: str
    tipo: str  # "pessoa", "empresa" ou "literal" (sem partes: cidade, e-mail, documento)

    @classmethod
    def pessoa(cls, valor: str | None, papel: str = "PESSOA") -> "Conhecido":
        return cls((valor or "").strip(), papel, "pessoa")

    @classmethod
    def empresa(cls, valor: str | None, papel: str = "EMPRESA") -> "Conhecido":
        return cls((valor or "").strip(), papel, "empresa")

    @classmethod
    def literal(cls, valor: str | None, papel: str = "DADO") -> "Conhecido":
        return cls((valor or "").strip(), papel, "literal")

    def partes(self) -> list[str]:
        palavras = self.valor.split()
        if self.tipo == "literal" or len(palavras) < 2:
            return []
        if self.tipo == "pessoa":
            return [p for p in palavras if len(p) >= 3 and p.lower() not in _CONECTORES]
        return [
            p
            for p in palavras
            if len(p) >= 4
            and p[0].isupper()
            and not p.isupper()
            and _sem_acento(p).lower().strip(".") not in _GENERICAS_DE_EMPRESA
        ]


# Formatos reconhecíveis, na ordem de preferência quando dois começam no mesmo lugar.
_LOGRADOURO = (
    r"(?i:rua|r\.|avenida|av\.|alameda|al\.|travessa|tv\.|rodovia|rod\.|estrada|estr\."
    r"|pra[cç]a|p[cç]a\.|largo|viela)"
)
_FORMATOS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    (
        "CNPJ",
        re.compile(
            r"(?<!\w)(?:[0-9A-Z]{2}\.[0-9A-Z]{3}\.[0-9A-Z]{3}/[0-9A-Z]{4}-\d{2}|\d{14})(?!\w)"
        ),
    ),
    ("CPF", re.compile(r"(?<![\w.])(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})(?!\w)")),
    ("CEP", re.compile(r"(?<![\w.])(?:\d{5}-\d{3}|\d{2}\.\d{3}-\d{3})(?!\w)")),
    (
        "TELEFONE",
        re.compile(
            r"(?<![\w+])(?:(?:\+?55[\s.-]?)?\(?0?\d{2}\)?[\s.-]?9?\d{4}[\s.-]?\d{4}"
            r"|9\d{4}[\s.-]?\d{4})(?!\w)"
        ),
    ),
    (
        "ENDERECO",
        re.compile(
            rf"(?<!\w){_LOGRADOURO}\s+(?:(?:d[aeo]s?)\s+)?[A-ZÀ-Ý0-9][^\n,;:().]{{0,60}}"
            r"(?:,\s*(?:n[º°o.]?\s*)?\d{1,6}[A-Za-z]?(?!\w))?"
        ),
    ),
]

# Categorias dos formatos reconhecidos; com os papéis, são os únicos prefixos de marcador.
# Outros colchetes do texto ("[IA]", "[revisão humana]" no fluxo to-be) não são marcadores.
_CATEGORIAS = ("PESSOA", "CIDADE", "DADO", "EMAIL", "CNPJ", "CPF", "CEP", "TELEFONE", "ENDERECO")
_MARCADOR = re.compile(r"\[(?:" + "|".join((*PAPEIS_UNICOS, *_CATEGORIAS)) + r")(?:_\d+)?\]")


def _chave_do_formato(categoria: str, trecho: str) -> str:
    """O mesmo documento escrito de dois jeitos ganha o mesmo marcador."""
    if categoria in {"CPF", "CNPJ", "CEP", "TELEFONE"}:
        return re.sub(r"[^0-9A-Z]", "", trecho.upper())
    return " ".join(_sem_acento(trecho).lower().split())


@dataclass(frozen=True)
class _Achado:
    inicio: int
    fim: int
    marcador: str | None  # None: formato reconhecido, marcador definido na hora
    categoria: str
    prioridade: int


@dataclass(frozen=True)
class Desfeito:
    texto: str
    desconhecidos: tuple[str, ...]  # marcadores da resposta que não vieram do texto enviado


class Anonimizador:
    def __init__(self, conhecidos: Sequence[Conhecido]):
        self._valor_do_marcador: dict[str, str] = {}
        self._marcador_do_formato: dict[tuple[str, str], str] = {}
        self._contagem: dict[str, int] = {}
        # (padrão, marcador): primeiro os valores inteiros, depois as partes; dentro de
        # cada grupo, os mais longos antes.
        inteiros: list[tuple[str, str]] = []
        partes: list[tuple[str, str]] = []
        vistos: set[str] = set()
        for conhecido in conhecidos:
            chave = " ".join(_sem_acento(conhecido.valor).lower().split())
            if not chave or chave in vistos:
                continue
            vistos.add(chave)
            marcador = self._novo_marcador(conhecido.papel, conhecido.valor)
            inteiros.append((conhecido.valor, marcador))
            for parte in conhecido.partes():
                chave_parte = _sem_acento(parte).lower()
                if chave_parte not in vistos:
                    vistos.add(chave_parte)
                    partes.append((parte, marcador))
        inteiros.sort(key=lambda par: -len(par[0]))
        partes.sort(key=lambda par: -len(par[0]))
        self._padroes_conhecidos = [
            (re.compile(_padrao_flexivel(valor), re.IGNORECASE), marcador)
            for valor, marcador in inteiros
        ] + [
            (re.compile(_padrao_flexivel(parte, maiuscula_inicial=True)), marcador)
            for parte, marcador in partes
        ]

    def _novo_marcador(self, papel: str, valor: str) -> str:
        # Só prefixos conhecidos: são os que `desfazer` reconhece na resposta.
        papel = papel.strip().upper()
        if papel not in PAPEIS_UNICOS and papel not in _CATEGORIAS:
            papel = "DADO"
        self._contagem[papel] = self._contagem.get(papel, 0) + 1
        n = self._contagem[papel]
        marcador = f"[{papel}]" if papel in PAPEIS_UNICOS and n == 1 else f"[{papel}_{n}]"
        self._valor_do_marcador[marcador] = valor
        return marcador

    @property
    def substituicoes(self) -> dict[str, str]:
        """Marcador → valor original (o que a prévia mostra ao consultor)."""
        return dict(self._valor_do_marcador)

    def _achados(self, texto: str) -> list[_Achado]:
        candidatos = [
            _Achado(m.start(), m.end(), marcador, "", i)
            for i, (padrao, marcador) in enumerate(self._padroes_conhecidos)
            for m in padrao.finditer(texto)
        ]
        base = len(self._padroes_conhecidos)
        candidatos += [
            _Achado(m.start(), m.end(), None, categoria, base + i)
            for i, (categoria, padrao) in enumerate(_FORMATOS)
            for m in padrao.finditer(texto)
        ]
        # Sem sobreposição: o que começa antes; empatando, o mais longo; depois a ordem.
        candidatos.sort(key=lambda a: (a.inicio, -(a.fim - a.inicio), a.prioridade))
        escolhidos: list[_Achado] = []
        fim = 0
        for achado in candidatos:
            if achado.inicio >= fim:
                escolhidos.append(achado)
                fim = achado.fim
        return escolhidos

    def anonimizar(self, texto: str) -> str:
        pedacos = []
        posicao = 0
        for achado in self._achados(texto):
            trecho = texto[achado.inicio : achado.fim]
            marcador = achado.marcador or self._marcador_de_formato(achado.categoria, trecho)
            pedacos += [texto[posicao : achado.inicio], marcador]
            posicao = achado.fim
        pedacos.append(texto[posicao:])
        return "".join(pedacos)

    def _marcador_de_formato(self, categoria: str, trecho: str) -> str:
        chave = (categoria, _chave_do_formato(categoria, trecho))
        if chave not in self._marcador_do_formato:
            self._marcador_do_formato[chave] = self._novo_marcador(categoria, trecho)
        return self._marcador_do_formato[chave]

    def restantes(self, texto: str) -> list[str]:
        """Trechos que ainda parecem dado pessoal (lista vazia: pode sair)."""
        return [texto[a.inicio : a.fim] for a in self._achados(texto)]

    def desfazer(self, texto: str) -> Desfeito:
        desconhecidos: list[str] = []

        def trocar(m: re.Match) -> str:
            marcador = m.group(0)
            if marcador in self._valor_do_marcador:
                return self._valor_do_marcador[marcador]
            if marcador not in desconhecidos:
                desconhecidos.append(marcador)
            return marcador

        return Desfeito(_MARCADOR.sub(trocar, texto), tuple(desconhecidos))


# --- Sugestão de nomes para a lista de pessoas citadas ---

# Palavras que aparecem com maiúscula no meio da frase e não são pessoas.
_DATAS = (
    "janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro "
    "dezembro segunda terca quarta quinta sexta sabado domingo"
)
_NAO_SAO_PESSOAS = {
    "brasil",
    "descoberta",
    "drive",
    "excel",
    "facebook",
    "google",
    "instagram",
    "linkedin",
    "meet",
    "outlook",
    "pix",
    "planilha",
    "proposta",
    "relatorio",
    "sessao",
    "teams",
    "whatsapp",
    "word",
    "zoom",
    *[
        "janeiro",
        "fevereiro",
        "marco",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
    ],
    *["dezembro", "segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"],
}
_PALAVRA_COM_MAIUSCULA = re.compile(r"(?<!\w)[A-ZÀ-Ý][a-zà-ÿ]{2,}(?!\w)")
_INICIO_DE_FRASE = re.compile(r"(?:^|[.!?:\n]\s*|^\s*[-•*\d.)]+\s*)$")


def sugerir_nomes(textos: Iterable[str], ignorar: Iterable[str] = ()) -> list[str]:
    """Palavras com maiúscula no meio da frase que podem ser nomes de pessoas.

    É só uma sugestão: o consultor confirma a lista. Nomes vizinhos viram um só ("Ana
    Paula"); começo de frase, siglas, ferramentas e o que já é conhecido ficam de fora.
    """
    ignorados = {_sem_acento(parte).lower() for valor in ignorar for parte in (valor or "").split()}
    nomes: list[str] = []
    for texto in textos:
        atual: list[str] = []
        fim_anterior = -1
        for m in _PALAVRA_COM_MAIUSCULA.finditer(texto):
            palavra = m.group(0)
            no_inicio = bool(_INICIO_DE_FRASE.search(texto[: m.start()]))
            continua = atual and texto[fim_anterior : m.start()] == " "
            if not continua:
                _guardar(atual, nomes, ignorados)
                atual = []
            if not no_inicio or continua:
                atual.append(palavra)
            fim_anterior = m.end()
        _guardar(atual, nomes, ignorados)
    return nomes


def _guardar(palavras: list[str], nomes: list[str], ignorados: set[str]) -> None:
    chaves = [_sem_acento(p).lower() for p in palavras]
    if not palavras or any(c in _NAO_SAO_PESSOAS or c in ignorados for c in chaves):
        return
    nome = " ".join(palavras)
    if nome not in nomes:
        nomes.append(nome)

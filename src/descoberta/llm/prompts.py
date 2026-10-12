"""Prompts versionados: um arquivo por versão, em prompts/<id>_v<n>.md.

Formato do arquivo:

    ---
    id: rascunho_revisao
    versao: 1
    descricao: ...
    campos: [titulo, contexto]     # os {{campos}} que o pedido usa
    alvos: {...}                   # opcional: orientações por alvo (proposta)
    ---
    # Sistema
    (instruções fixas)
    # Pedido
    (mensagem com {{campos}})

O texto fica fora do código, como o questionário; o código só confere e preenche. Cada
rascunho guarda o rótulo do prompt usado ("rascunho_revisao_v1"). Para mudar um prompt,
crie a versão seguinte em vez de editar a que já foi usada.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from descoberta.questionario.carregador import ArquivoInvalido

_NOME = re.compile(r"(?P<id>[a-z0-9_]+?)_v(?P<versao>\d+)\.md")
_CAMPO = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")
_SECAO = re.compile(r"^# (Sistema|Pedido)\s*$", re.MULTILINE)


class PromptInvalido(ArquivoInvalido):
    NOME = "Prompt"


@dataclass(frozen=True)
class Pedido:
    """O que vai ao provedor: as instruções fixas e a mensagem do pedido."""

    sistema: str
    mensagem: str


@dataclass(frozen=True)
class Prompt:
    id: str
    versao: int
    descricao: str
    sistema: str
    pedido: str
    campos: tuple[str, ...]
    alvos: dict[str, str] = field(default_factory=dict)

    @property
    def rotulo(self) -> str:
        return f"{self.id}_v{self.versao}"

    def preencher(self, **valores: str) -> Pedido:
        """Troca os {{campos}} pelos valores (todos os declarados, nenhum a mais)."""
        faltando = [c for c in self.campos if c not in valores]
        if faltando:
            raise ValueError(f"prompt {self.rotulo}: falta o campo '{faltando[0]}'")
        extras = sorted(set(valores) - set(self.campos))
        if extras:
            raise ValueError(f"prompt {self.rotulo}: campo desconhecido '{extras[0]}'")
        # Uma passada só: um valor que contenha "{{x}}" não é preenchido de novo.
        mensagem = _CAMPO.sub(lambda m: str(valores[m.group(1)]), self.pedido)
        return Pedido(self.sistema, mensagem)


def carregar_prompt(caminho: Path | str) -> Prompt:
    caminho = Path(caminho)
    nome = _NOME.fullmatch(caminho.name)
    if nome is None:
        raise PromptInvalido(caminho, ["o nome do arquivo deve ser <id>_v<número>.md"])
    texto = caminho.read_text(encoding="utf-8").replace("\r\n", "\n")
    partes = texto.split("---\n", 2)
    if not texto.startswith("---\n") or len(partes) < 3:
        raise PromptInvalido(caminho, ["falta o cabeçalho entre linhas '---' no início"])
    try:
        cabecalho = yaml.safe_load(partes[1]) or {}
    except yaml.YAMLError as erro:
        raise PromptInvalido(caminho, [f"cabeçalho mal formado: {erro}"]) from erro
    return _validar(caminho, nome, cabecalho, partes[2])


def _validar(caminho: Path, nome: re.Match, cabecalho: dict, corpo: str) -> Prompt:
    erros: list[str] = []
    versao = cabecalho.get("versao")
    if not isinstance(versao, int):
        erros.append(f"versao deve ser um número inteiro (recebido {versao!r})")
    elif versao != int(nome.group("versao")):
        erros.append(f"o cabeçalho diz versão {versao}, mas o nome do arquivo diz outra")
    if cabecalho.get("id") != nome.group("id"):
        erros.append(f"o id {cabecalho.get('id')!r} não bate com o nome do arquivo")
    campos = cabecalho.get("campos") or []
    alvos = cabecalho.get("alvos") or {}

    secoes = _SECAO.split(corpo)
    # split devolve: [antes, "Sistema", texto, "Pedido", texto]
    titulos = secoes[1::2]
    if titulos != ["Sistema", "Pedido"]:
        erros.append("o corpo deve ter as seções '# Sistema' e '# Pedido', nessa ordem")
        sistema = pedido = ""
    else:
        sistema, pedido = (s.strip() for s in secoes[2::2])
        usados = set(_CAMPO.findall(pedido))
        for campo in sorted(usados - set(campos)):
            erros.append(f"o pedido usa {{{{{campo}}}}}, que não está em campos")
        for campo in sorted(set(campos) - usados):
            erros.append(f"o campo {campo!r} está em campos, mas o pedido não o usa")
        if _CAMPO.search(sistema):
            erros.append("a seção '# Sistema' não pode ter {{campos}}")
    if erros:
        raise PromptInvalido(caminho, erros)
    return Prompt(
        id=cabecalho["id"],
        versao=versao,
        descricao=str(cabecalho.get("descricao", "")),
        sistema=sistema,
        pedido=pedido,
        campos=tuple(campos),
        alvos={str(k): " ".join(str(v).split()) for k, v in alvos.items()},
    )


def carregar_prompts(pasta: Path | str) -> dict[str, Prompt]:
    """Todos os prompts da pasta, na versão mais recente de cada id.

    Arquivos com outro nome (um LEIA-ME.md, por exemplo) são ignorados.
    """
    prompts: dict[str, Prompt] = {}
    for caminho in sorted(Path(pasta).glob("*.md")):
        if _NOME.fullmatch(caminho.name) is None:
            continue
        prompt = carregar_prompt(caminho)
        if prompt.id not in prompts or prompt.versao > prompts[prompt.id].versao:
            prompts[prompt.id] = prompt
    return prompts

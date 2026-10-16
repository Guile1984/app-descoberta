"""Procura dados pessoais em TODO o histórico do Git (todas as branches e versões).

Uso (na raiz do projeto):

    uv run python scripts/revisar_historico.py

Passa o conteúdo de cada versão de cada arquivo já versionado pelo mesmo detector da
anonimização do LLM (CPF, CNPJ, e-mail, telefone, CEP e endereço), sem internet. Mostra
cada valor encontrado uma vez, com os arquivos onde aparece, separando o que é fictício
de propósito (domínios example.*, números de teste do demo) do que precisa ser conferido
à mão. Complementa o gitleaks, que procura segredos (chaves, senhas, tokens).

O resultado aparece só no terminal: não grave a saída no repositório.
"""

import re
import subprocess
import sys
from collections import defaultdict

from descoberta.llm.anonimizacao import Anonimizador

# Fictícios conhecidos: domínios reservados para exemplo (RFC 2606) e os números de teste
# do demo e dos testes, todos documentados no código onde aparecem.
_DOMINIOS_DE_EXEMPLO = re.compile(r"@([\w.-]+\.)?(example|exemplo)(\.[a-z.]+)?$|\.example$", re.I)
FICTICIOS = {
    "11.222.333/0001-81",  # CNPJ clássico de teste (demo)
    "12.ABC.345/01DE-35",  # CNPJ alfanumérico de exemplo da Receita (demo)
    "(11) 90000-0000",  # telefone do consultor fictício (demo)
}
# Dados reais publicados de propósito, por escolha do autor: aparecem à parte no resultado.
PUBLICOS = {
    "guilherme.stauffer@hotmail.com",  # contato do CODE_OF_CONDUCT.md (Sprint 9)
}


def _git(*argumentos: str, entrada: bytes | None = None) -> bytes:
    return subprocess.run(  # noqa: S603 (argumentos fixos, sem shell)
        ["git", *argumentos],  # noqa: S607 (git do PATH, como em todo o projeto)
        input=entrada,
        capture_output=True,
        check=True,
    ).stdout


def blobs_do_historico() -> dict[str, set[str]]:
    """Cada versão de arquivo (blob) de todas as branches, com os caminhos onde apareceu."""
    caminhos: dict[str, set[str]] = defaultdict(set)
    for linha in _git("rev-list", "--all", "--objects").decode("utf-8").splitlines():
        objeto, _, caminho = linha.partition(" ")
        if caminho:
            caminhos[objeto].add(caminho)
    tipos = _git("cat-file", "--batch-check", entrada="\n".join(caminhos).encode()).decode()
    blobs = {linha.split()[0] for linha in tipos.splitlines() if linha.split()[1] == "blob"}
    return {objeto: caminhos[objeto] for objeto in blobs}


def conteudo(objeto: str) -> str | None:
    dados = _git("cat-file", "blob", objeto)
    try:
        return dados.decode("utf-8")
    except UnicodeDecodeError:
        return None  # binário (PDF, fonte, imagem): o gitleaks também não lê


def ficticio(valor: str) -> bool:
    return valor in FICTICIOS or bool(_DOMINIOS_DE_EXEMPLO.search(valor.strip()))


def main() -> int:
    detector = Anonimizador([])
    achados: dict[str, set[str]] = defaultdict(set)
    blobs = blobs_do_historico()
    binarios = 0
    for objeto, caminhos in blobs.items():
        texto = conteudo(objeto)
        if texto is None:
            binarios += 1
            continue
        for valor in detector.restantes(texto):
            achados[" ".join(valor.split())].update(caminhos)

    publicos = {v for v in achados if v in PUBLICOS}
    conferir = {v: c for v, c in achados.items() if not ficticio(v) and v not in publicos}
    print(f"Versões de arquivo lidas: {len(blobs) - binarios} de texto, {binarios} binárias.")
    print(f"Valores fictícios conhecidos: {len(achados) - len(conferir) - len(publicos)}.")
    print(f"Contatos públicos de propósito: {', '.join(sorted(publicos)) or 'nenhum'}.")
    print(f"Para conferir à mão: {len(conferir)}.\n")
    for valor, caminhos in sorted(conferir.items()):
        print(f"- {valor!r}")
        for caminho in sorted(caminhos):
            print(f"    {caminho}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

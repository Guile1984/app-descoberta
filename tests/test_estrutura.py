"""Testes de estrutura do projeto: pacote instalável e regras de arquitetura."""

import ast
from pathlib import Path

import pytest

import descoberta

RAIZ_PACOTE = Path(descoberta.__file__).parent

# Dependências apontam para dentro: cada camada lista as camadas que ela não pode importar.
CAMADAS_PROIBIDAS = {
    "dominio": {"web", "repositorio", "llm"},
    "repositorio": {"web", "llm", "relatorio"},
}


def test_pacote_importavel():
    assert isinstance(descoberta.__version__, str)
    assert descoberta.__version__


def modulos_importados(codigo: str, pacote: str) -> set[str]:
    """Retorna os nomes completos dos módulos importados por um código Python.

    `pacote` é o pacote onde o código está (ex.: "descoberta.dominio"), usado para
    resolver imports relativos como `from ..web import x`.
    """
    modulos: set[str] = set()
    for no in ast.walk(ast.parse(codigo)):
        if isinstance(no, ast.Import):
            modulos.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom):
            if no.level > 0:
                partes = pacote.split(".")
                base = partes[: len(partes) - (no.level - 1)]
                modulos.add(".".join([*base, no.module] if no.module else base))
            elif no.module:
                modulos.add(no.module)
    return modulos


def violacoes(modulos: set[str], proibidas: set[str]) -> list[str]:
    encontradas = []
    for modulo in modulos:
        partes = modulo.split(".")
        eh_do_projeto = len(partes) > 1 and partes[0] == "descoberta"
        if eh_do_projeto and partes[1] in proibidas:
            encontradas.append(modulo)
    return sorted(encontradas)


def test_detector_encontra_imports_proibidos():
    codigo = (
        "import descoberta.web.app\n"
        "from descoberta.repositorio import banco\n"
        "from ..llm import provedor\n"
        "from . import calculos\n"
        "import math\n"
    )
    modulos = modulos_importados(codigo, "descoberta.dominio")
    assert violacoes(modulos, CAMADAS_PROIBIDAS["dominio"]) == [
        "descoberta.llm",
        "descoberta.repositorio",
        "descoberta.web.app",
    ]


@pytest.mark.parametrize("camada", sorted(CAMADAS_PROIBIDAS))
def test_camada_nao_importa_camadas_externas(camada):
    proibidas = CAMADAS_PROIBIDAS[camada]
    encontradas = []
    for arquivo in sorted((RAIZ_PACOTE / camada).rglob("*.py")):
        # O pacote de um arquivo é a pasta onde ele está (vale também para __init__.py).
        pacote = ".".join(arquivo.relative_to(RAIZ_PACOTE.parent).parent.parts)
        codigo = arquivo.read_text(encoding="utf-8")
        for modulo in violacoes(modulos_importados(codigo, pacote), proibidas):
            encontradas.append(f"{arquivo.name}: {modulo}")
    assert not encontradas, f"{camada} não pode importar {sorted(proibidas)}: {encontradas}"

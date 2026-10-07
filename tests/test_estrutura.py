"""Testes de estrutura do projeto: pacote instalável e regras de arquitetura."""

import ast
from pathlib import Path

import descoberta

RAIZ_PACOTE = Path(descoberta.__file__).parent
CAMADAS_PROIBIDAS_NO_DOMINIO = {"web", "repositorio", "llm"}


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


def violacoes_do_dominio(modulos: set[str]) -> list[str]:
    violacoes = []
    for modulo in modulos:
        partes = modulo.split(".")
        eh_do_projeto = len(partes) > 1 and partes[0] == "descoberta"
        if eh_do_projeto and partes[1] in CAMADAS_PROIBIDAS_NO_DOMINIO:
            violacoes.append(modulo)
    return sorted(violacoes)


def test_detector_encontra_imports_proibidos():
    codigo = (
        "import descoberta.web.app\n"
        "from descoberta.repositorio import banco\n"
        "from ..llm import provedor\n"
        "from . import calculos\n"
        "import math\n"
    )
    modulos = modulos_importados(codigo, "descoberta.dominio")
    assert violacoes_do_dominio(modulos) == [
        "descoberta.llm",
        "descoberta.repositorio",
        "descoberta.web.app",
    ]


def test_dominio_nao_importa_camadas_externas():
    violacoes = []
    for arquivo in sorted((RAIZ_PACOTE / "dominio").rglob("*.py")):
        # O pacote de um arquivo é a pasta onde ele está (vale também para __init__.py).
        pacote = ".".join(arquivo.relative_to(RAIZ_PACOTE.parent).parent.parts)
        codigo = arquivo.read_text(encoding="utf-8")
        for modulo in violacoes_do_dominio(modulos_importados(codigo, pacote)):
            violacoes.append(f"{arquivo.name}: {modulo}")
    assert not violacoes, f"dominio não pode importar web/repositorio/llm: {violacoes}"

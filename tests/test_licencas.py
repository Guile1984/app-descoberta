"""Licenças: a do projeto e a de cada componente de terceiros.

O código é MIT; a metodologia (Modelo de Descoberta e conteúdo do questionário) é CC BY 4.0.
Este teste falha se entrar uma dependência com licença fora da lista permitida (por
exemplo, GPL, que obrigaria a abrir o código de quem distribuísse a app junto com ela), ou
se o htmx copiado no repositório mudar sem atualizar o THIRD_PARTY_NOTICES.md.
"""

import hashlib
import re
import tomllib
from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

# Licenças permissivas: permitem usar, modificar e distribuir, pedindo no máximo o aviso.
# MPL-2.0 é "copyleft fraco" por arquivo: só obriga a abrir mudanças nos próprios arquivos
# da biblioteca (certifi, a lista de certificados), que usamos sem modificar.
PERMITIDAS = {
    "0BSD",
    "Apache-2.0",
    "BSD",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "MIT",
    "MIT-CMU",
    "MPL-2.0",
    "PSF-2.0",
}

# Só nas ferramentas de desenvolvimento (não vão com a app), conferidas uma a uma.
EXCECOES_DESENVOLVIMENTO = {
    # Dupla licença (Artistic ou GPL); vem com o pytest-playwright (via python-slugify).
    # Usada só para rodar os testes, nunca distribuída: vale a opção Artistic.
    "text-unidecode": "Artistic-1.0 OR GPL-2.0-or-later",
}

_CLASSIFICADORES = {
    "MIT License": "MIT",
    "BSD License": "BSD",
    "Apache Software License": "Apache-2.0",
    "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "Python Software Foundation License": "PSF-2.0",
    "ISC License (ISCL)": "ISC",
}


def _lock() -> dict[str, dict]:
    dados = tomllib.loads((RAIZ / "uv.lock").read_text(encoding="utf-8"))
    return {pacote["name"]: pacote for pacote in dados["package"]}


def _fechamento(lock: dict[str, dict], nomes: list[str]) -> set[str]:
    """Os pacotes e tudo de que eles dependem (sem olhar marcadores: inclui os de outros SOs)."""
    vistos: set[str] = set()
    pendentes = list(nomes)
    while pendentes:
        nome = pendentes.pop()
        if nome in vistos:
            continue
        vistos.add(nome)
        pendentes += [d["name"] for d in lock[nome].get("dependencies", [])]
        for extras in lock[nome].get("optional-dependencies", {}).values():
            pendentes += [d["name"] for d in extras]
    return vistos


def _dependencias() -> tuple[set[str], set[str]]:
    lock = _lock()
    projeto = lock["descoberta"]
    execucao = _fechamento(lock, [d["name"] for d in projeto["dependencies"]])
    desenvolvimento = _fechamento(
        lock, [d["name"] for grupo in projeto["dev-dependencies"].values() for d in grupo]
    )
    return execucao, desenvolvimento - execucao


def licenca(pacote: str) -> str | None:
    """A licença declarada pelo pacote instalado (None se não estiver instalado aqui)."""
    try:
        dados = metadata(pacote)
    except PackageNotFoundError:
        return None  # dependência de outro sistema (ex.: colorama, só no Windows)
    if expressao := dados.get("License-Expression"):
        return expressao
    classificadores = [
        _CLASSIFICADORES.get(c.split(" :: ")[-1], c.split(" :: ")[-1])
        for c in dados.get_all("Classifier") or []
        if c.startswith("License ::") and c != "License :: OSI Approved"
    ]
    if classificadores:
        return " OR ".join(dict.fromkeys(classificadores))
    texto = (dados.get("License") or "").strip()
    return texto if texto in PERMITIDAS else f"desconhecida: {texto[:40]!r}"


def permitida(expressao: str) -> bool:
    """ "A OR B": basta uma permitida; "A AND B": todas precisam ser."""
    alternativas = re.split(r"\s+OR\s+", expressao.strip("() "))
    return any(
        all(parte.strip("() ") in PERMITIDAS for parte in re.split(r"\s+AND\s+", alternativa))
        for alternativa in alternativas
    )


@pytest.mark.parametrize(
    ("expressao", "esperado"),
    [
        ("MIT", True),
        ("Apache-2.0 OR BSD-2-Clause", True),
        ("MIT AND PSF-2.0", True),
        ("GPL-3.0-only", False),
        ("MIT AND GPL-2.0-or-later", False),
        ("GPL-2.0-or-later OR MIT", True),
        ("desconhecida: ''", False),
    ],
)
def test_regra_das_licencas(expressao, esperado):
    assert permitida(expressao) is esperado


def test_dependencias_da_app_tem_licenca_permissiva():
    execucao, _ = _dependencias()
    problemas = {
        pacote: lic
        for pacote in sorted(execucao)
        if (lic := licenca(pacote)) is not None and not permitida(lic)
    }
    assert problemas == {}


def test_ferramentas_de_desenvolvimento_permissivas_ou_conferidas():
    _, desenvolvimento = _dependencias()
    problemas = {
        pacote: lic
        for pacote in sorted(desenvolvimento)
        if (lic := licenca(pacote)) is not None
        and not permitida(lic)
        and pacote not in EXCECOES_DESENVOLVIMENTO
    }
    assert problemas == {}


def test_excecoes_ainda_sao_necessarias():
    # Se a exceção deixou de ser usada, ela sai da lista (não fica liberando nada à toa).
    _, desenvolvimento = _dependencias()
    assert set(EXCECOES_DESENVOLVIMENTO) <= desenvolvimento


def test_licenca_do_projeto_e_mit():
    texto = (RAIZ / "LICENSE").read_text(encoding="utf-8")
    assert texto.startswith("MIT License")
    assert "Copyright (c) 2026 Guilherme Ferraz Stauffer" in texto
    projeto = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert projeto["license"] == "MIT"


def test_metodologia_em_cc_by():
    texto = (RAIZ / "LICENSE-METODOLOGIA.md").read_text(encoding="utf-8")
    assert "CC BY 4.0" in texto
    assert "https://creativecommons.org/licenses/by/4.0/" in texto
    for arquivo in ("docs/modelo-descoberta.md", "config/questionario_v1.yaml"):
        assert arquivo in texto
        assert "CC BY 4.0" in (RAIZ / arquivo).read_text(encoding="utf-8")[:1500], arquivo


def test_avisos_de_terceiros_cobrem_o_que_vai_no_repositorio():
    avisos = (RAIZ / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    htmx = (RAIZ / "src/descoberta/web/static/htmx.min.js").read_bytes()
    versao = re.search(rb'version:"([0-9.]+)"', htmx).group(1).decode()
    assert f"htmx {versao}" in avisos
    assert hashlib.sha256(htmx).hexdigest() in avisos  # o arquivo é o oficial, sem mudança
    assert "Zero-Clause BSD" in avisos
    assert "DejaVu" in avisos
    assert "src/descoberta/relatorio/fontes/LICENSE-DejaVu.txt" in avisos
    assert (RAIZ / "src/descoberta/relatorio/fontes/LICENSE-DejaVu.txt").exists()


def test_avisos_de_terceiros_listam_as_dependencias_da_app():
    avisos = (RAIZ / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8").lower()
    execucao, _ = _dependencias()
    faltando = sorted(p for p in execucao if f"| {p.lower()} |" not in avisos)
    assert faltando == []

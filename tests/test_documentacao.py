"""A documentação (site MkDocs em docs/) confere com o código.

Cada teste compara uma página de referência com a fonte de verdade no código: se alguém
cria um atalho, um campo no YAML, uma tabela no banco ou uma variável de ambiente e
esquece a documentação, o teste falha e diz o que falta. O texto explicativo das páginas
é conferido à mão; aqui ficam os fatos que dá para conferir automaticamente.
"""

import re
import types
import typing
from fnmatch import fnmatch
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel
from sqlmodel import SQLModel

import descoberta.repositorio.modelos  # noqa: F401  (registra as tabelas no metadata)
from descoberta.llm.configuracao import VARIAVEL_CHAVE, VARIAVEL_PROVEDOR, ConfiguracaoLLM
from descoberta.proposta import carregar_modelo_proposta
from descoberta.proposta.modelos import MARCADORES, ModeloProposta
from descoberta.questionario import Questionario
from descoberta.web.atalhos import ATALHOS

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
SITE = "https://guile1984.github.io/app-descoberta/"
# Arquivos que os guias mandam criar (a próxima versão), citados como exemplo.
EXEMPLOS = {"config/questionario_v2.yaml", "config/proposta_v2.yaml"}

# As quatro partes do Diátaxis e as páginas que cada uma precisa ter (Sprint 9).
PAGINAS = {
    "Tutorial": ["tutorial/primeira-sessao.md"],
    "Guias práticos": [
        "guias/sessao-ao-vivo.md",
        "guias/revisao-pos-sessao.md",
        "guias/relatorio-e-proposta.md",
        "guias/adaptar-questionario.md",
        "guias/adaptar-clausulas.md",
        "guias/configurar-llm.md",
        "guias/backup-e-restauracao.md",
        "guias/atualizar-a-app.md",
    ],
    "Referência": [
        "referencia/atalhos.md",
        "referencia/yaml.md",
        "referencia/formulas-e-scores.md",
        "referencia/modelo-de-dados.md",
        "referencia/ambiente-e-comandos.md",
    ],
    "Explicação": [
        "explicacao/metodologia.md",
        "modelo-descoberta.md",
        "explicacao/arquitetura.md",
        "explicacao/privacidade-lgpd.md",
        "qualidade/evidencias.md",
        "explicacao/uso-em-producao.md",
    ],
}


# --- Utilitários ---


class _Carregador(yaml.SafeLoader):
    """Lê o mkdocs.yml, que usa tags !!python/name: para algumas extensões."""


_Carregador.add_multi_constructor(
    "tag:yaml.org,2002:python/", lambda carregador, sufixo, no: sufixo
)


def mkdocs() -> dict:
    return yaml.load((RAIZ / "mkdocs.yml").read_text(encoding="utf-8"), _Carregador)  # noqa: S506


def pagina(caminho: str) -> str:
    return (DOCS / caminho).read_text(encoding="utf-8")


def secao(texto: str, inicio_do_titulo: str) -> str:
    """O trecho de um título Markdown (que começa com `inicio_do_titulo`) até o próximo
    título do mesmo nível ou acima."""
    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        marca = re.match(r"(#+) ", linha)
        if marca and linha[marca.end() :].startswith(inicio_do_titulo):
            nivel = len(marca.group(1))
            fim = next(
                (
                    j
                    for j in range(i + 1, len(linhas))
                    if (m := re.match(r"(#+) ", linhas[j])) and len(m.group(1)) <= nivel
                ),
                len(linhas),
            )
            return "\n".join(linhas[i:fim])
    raise AssertionError(f"título que começa com {inicio_do_titulo!r} não encontrado")


def padroes(chave: str) -> list[str]:
    """As linhas (no formato do .gitignore) de not_in_nav ou exclude_docs do mkdocs.yml."""
    return [
        linha.strip().lstrip("/")
        for linha in mkdocs().get(chave, "").splitlines()
        if linha.strip() and not linha.strip().startswith("#")
    ]


def paginas_do_site() -> list[str]:
    """As páginas .md de docs/ que vão para o site (sem as de exclude_docs)."""
    fora = padroes("exclude_docs")
    return [
        relativo
        for arquivo in sorted(DOCS.rglob("*.md"))
        if not any(fnmatch(relativo := arquivo.relative_to(DOCS).as_posix(), p) for p in fora)
    ]


def arquivos_do_nav(nav) -> list[str]:
    if isinstance(nav, str):
        return [nav]
    if isinstance(nav, list):
        return [arquivo for item in nav for arquivo in arquivos_do_nav(item)]
    if isinstance(nav, dict):
        return [arquivo for valor in nav.values() for arquivo in arquivos_do_nav(valor)]
    return []


def campos(modelo: type[BaseModel]) -> set[str]:
    """Os nomes de todos os campos do modelo e dos modelos dentro dele (o que vai no YAML)."""
    nomes: set[str] = set()
    vistos: set[type] = set()

    def visitar(tipo) -> None:
        if isinstance(tipo, type) and issubclass(tipo, BaseModel):
            if tipo in vistos:
                return
            vistos.add(tipo)
            for nome, info in tipo.model_fields.items():
                nomes.add(nome)
                visitar(info.annotation)
        for argumento in typing.get_args(tipo):
            visitar(argumento)
        if isinstance(tipo, types.UnionType):
            for argumento in tipo.__args__:
                visitar(argumento)

    visitar(modelo)
    return nomes


def em_codigo(nome: str, texto: str) -> bool:
    """O nome aparece como código (`nome`) no texto."""
    return f"`{nome}`" in texto


# --- Organização do site ---


def test_site_organizado_no_diataxis():
    nav = mkdocs()["nav"]
    secoes = {
        titulo: arquivos_do_nav(conteudo)
        for item in nav
        if isinstance(item, dict)
        for titulo, conteudo in item.items()
    }
    for titulo, esperadas in PAGINAS.items():
        assert titulo in secoes, f"o menu não tem a seção {titulo!r}"
        faltam = [p for p in esperadas if p not in secoes[titulo]]
        assert faltam == [], f"{titulo}: faltam no menu {faltam}"


def test_toda_pagina_do_menu_existe():
    faltam = [p for p in arquivos_do_nav(mkdocs()["nav"]) if not (DOCS / p).is_file()]
    assert faltam == []


def test_nenhuma_pagina_esquecida_fora_do_menu():
    # Toda página do site está no menu ou fora dele de propósito (not_in_nav); as demais
    # ficam fora do site (exclude_docs). Assim uma página nova não fica perdida, sem link.
    no_menu = set(arquivos_do_nav(mkdocs()["nav"]))
    fora_do_menu = padroes("not_in_nav")
    esquecidas = [
        relativo
        for relativo in paginas_do_site()
        if relativo not in no_menu and not any(fnmatch(relativo, p) for p in fora_do_menu)
    ]
    assert esquecidas == []


def test_site_em_portugues_e_estrito():
    config = mkdocs()
    assert config["site_url"] == SITE
    assert config["theme"]["name"] == "material"
    assert config["theme"]["language"] == "pt-BR"
    # Sem Google Fonts: a visita do leitor não é contada pelo Google.
    assert config["theme"]["font"] is False
    assert config["strict"] is True
    assert config["docs_dir"] == "docs"


def test_caminhos_citados_existem():
    # `src/descoberta/web/atalhos.py`, `config/llm.yaml`... citados nas páginas existem
    # de verdade (modelos com <id>, {n} ou * são exemplos, não arquivos).
    citados = re.compile(r"`((?:src|config|prompts|scripts|tests|docs|\.github)/[^`\s]+)`")
    inexistentes = []
    for relativo in paginas_do_site():
        for caminho in citados.findall(pagina(relativo)):
            caminho = caminho.split("::")[0].rstrip("/")
            if re.search(r"[<>{}*]|NNNN", caminho) or caminho in EXEMPLOS:
                continue
            if not (RAIZ / caminho).exists():
                inexistentes.append(f"{relativo}: {caminho}")
    assert inexistentes == []


# --- Referência ---


def test_todo_atalho_documentado():
    texto = pagina("referencia/atalhos.md")
    faltam = [a.teclas for a in ATALHOS if em_codigo(a.teclas, texto) is False]
    assert faltam == []
    # Uma linha da tabela por atalho: nenhum atalho a mais, que não exista na app.
    linhas = [linha for linha in texto.splitlines() if re.match(r"\|\s*`", linha)]
    assert len(linhas) == len(ATALHOS)


@pytest.mark.parametrize(
    ("titulo", "modelo"),
    [
        ("Questionário", Questionario),
        ("Modelo da proposta", ModeloProposta),
        ("Configuração do LLM", ConfiguracaoLLM),
    ],
)
def test_todo_campo_do_yaml_documentado(titulo, modelo):
    texto = secao(pagina("referencia/yaml.md"), titulo)
    faltam = sorted(nome for nome in campos(modelo) if not em_codigo(nome, texto))
    assert faltam == [], f"{titulo}: campos sem documentação"


def test_marcadores_das_clausulas_documentados():
    for texto in (pagina("referencia/yaml.md"), pagina("guias/adaptar-clausulas.md")):
        faltam = [m for m in MARCADORES if not em_codigo(f"{{{m}}}", texto)]
        assert faltam == []


def test_clausulas_que_nao_podem_ser_excluidas_listadas():
    modelo = carregar_modelo_proposta(RAIZ / "config" / "proposta_v1.yaml")
    texto = secao(pagina("guias/adaptar-clausulas.md"), "Cláusulas que não podem ser excluídas")
    fixas = [c for c in modelo.clausulas if not c.removivel]
    faltam = [c.titulo for c in fixas if c.titulo not in texto]
    assert faltam == []
    sobram = [c.titulo for c in modelo.clausulas if c.removivel and c.titulo in texto]
    assert sobram == []


def test_toda_tabela_e_coluna_do_banco_documentada():
    texto = pagina("referencia/modelo-de-dados.md")
    tabelas = SQLModel.metadata.tables
    documentadas = set(re.findall(r"^### `(\w+)`", texto, re.M))
    assert documentadas == set(tabelas), "tabelas a mais ou a menos na página"
    faltam = [
        f"{nome}.{coluna.name}"
        for nome, tabela in tabelas.items()
        for coluna in tabela.columns
        if not em_codigo(coluna.name, secao(texto, f"`{nome}`"))
    ]
    assert faltam == []


def test_variaveis_de_ambiente_documentadas():
    lidas = {VARIAVEL_CHAVE, VARIAVEL_PROVEDOR}
    for arquivo in (RAIZ / "src").rglob("*.py"):
        lidas |= set(re.findall(r"[\"'](DESCOBERTA_[A-Z_]+)[\"']", arquivo.read_text("utf-8")))
    exemplo = (RAIZ / ".env.example").read_text(encoding="utf-8")
    lidas |= set(re.findall(r"^([A-Z_]+)=", exemplo, re.M))
    texto = pagina("referencia/ambiente-e-comandos.md")
    assert sorted(v for v in lidas if not em_codigo(v, texto)) == []


def test_opcoes_de_linha_de_comando_documentadas():
    opcoes = set()
    for arquivo in [*(RAIZ / "src").rglob("*.py"), *(RAIZ / "scripts").glob("*.py")]:
        opcoes |= set(re.findall(r"add_argument\(\s*\"(--[\w-]+)\"", arquivo.read_text("utf-8")))
    assert opcoes, "nenhuma opção encontrada: a busca mudou?"
    texto = pagina("referencia/ambiente-e-comandos.md")
    assert sorted(o for o in opcoes if not em_codigo(o, texto)) == []


def _linha_da_faixa(texto: str, minimo: int, maximo: int, valor: str) -> bool:
    padrao = rf"\|\s*{minimo}\s*–\s*{maximo}\s*\|\s*{re.escape(valor)}\s*\|"
    return re.search(padrao, texto) is not None


def test_faixas_e_criterios_dos_scores_como_no_questionario(questionario_v1):
    texto = pagina("referencia/formulas-e-scores.md")
    dados = questionario_v1.scores.prontidao_dados
    final = questionario_v1.scores.viabilidade_final
    for nome, score in (("Score de prontidão de dados", dados), ("Score final", final)):
        trecho = secao(texto, nome)
        assert f"máximo {score.pontuacao_maxima}" in trecho, nome
        for criterio in score.criterios:
            assert criterio.rotulo in trecho, f"{nome}: critério {criterio.rotulo!r}"
        for faixa in score.faixas:
            assert _linha_da_faixa(trecho, faixa.min, faixa.max, faixa.rotulo), (
                f"{nome}: faixa {faixa.min}–{faixa.max} ({faixa.rotulo})"
            )
    trecho = secao(texto, "Score de prontidão de dados")
    for faixa in dados.conversao_para_nota:
        assert _linha_da_faixa(trecho, faixa.min, faixa.max, str(faixa.nota)), (
            f"conversão {faixa.min}–{faixa.max} → {faixa.nota}"
        )


def test_duracao_da_sessao_como_no_questionario(questionario_v1):
    texto = pagina("guias/sessao-ao-vivo.md")
    assert f"{questionario_v1.duracao.aviso_minutos} min" in texto
    assert f"{questionario_v1.duracao.limite_minutos} min" in texto


# --- Porta de entrada e arquivos da comunidade ---


def test_readme_aponta_para_o_site_e_para_o_guia_de_producao():
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert SITE in readme
    assert f"{SITE}explicacao/uso-em-producao/" in readme
    for arquivo in ("README.md", "SECURITY.md"):
        assert "Sprint 9" not in (RAIZ / arquivo).read_text(encoding="utf-8"), arquivo


def test_arquivos_da_comunidade():
    assert "uv run --group docs mkdocs serve" in (RAIZ / "CONTRIBUTING.md").read_text("utf-8")
    conduta = (RAIZ / "CODE_OF_CONDUCT.md").read_text(encoding="utf-8")
    assert "guilherme.stauffer@hotmail.com" in conduta
    assert (RAIZ / ".github" / "pull_request_template.md").is_file()


def test_modelos_de_issue_validos():
    pasta = RAIZ / ".github" / "ISSUE_TEMPLATE"
    config = yaml.safe_load((pasta / "config.yml").read_text(encoding="utf-8"))
    assert config["blank_issues_enabled"] is False
    formularios = sorted(pasta.glob("*.yml"))
    formularios.remove(pasta / "config.yml")
    assert len(formularios) >= 2
    for arquivo in formularios:
        dados = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        assert {"name", "description", "body"} <= dados.keys(), arquivo.name
        # Quem relata um problema é lembrado de não colar dados de clientes.
        assert "dados fictícios" in arquivo.read_text(encoding="utf-8"), arquivo.name


def test_ci_da_documentacao():
    texto = (RAIZ / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")
    assert "mkdocs build --strict" in texto
    assert "lychee" in texto
    fluxo = yaml.safe_load(texto)
    publicar = fluxo["jobs"]["publicar"]
    # Publica só o que chegou na main, e só depois de compilar sem avisos.
    assert publicar["needs"] == "compilar"
    assert "refs/heads/main" in publicar["if"]
    assert "push" in publicar["if"]

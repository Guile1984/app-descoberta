"""Prompts versionados em arquivo (prompts/<id>_v<n>.md)."""

from pathlib import Path

import pytest

from descoberta.llm.prompts import PromptInvalido, carregar_prompt, carregar_prompts

VALIDO = """---
id: teste
versao: 2
descricao: Prompt de teste.
campos: [nome]
---

# Sistema

Seja breve.

# Pedido

Olá, {{nome}}.
"""


def _escrever(pasta: Path, nome: str, texto: str) -> Path:
    caminho = pasta / nome
    caminho.write_text(texto, encoding="utf-8")
    return caminho


RAIZ = Path(__file__).resolve().parents[2]


def test_prompts_do_projeto_na_versao_2(prompts):
    assert set(prompts) == {"rascunho_revisao", "rascunho_proposta"}
    revisao = prompts["rascunho_revisao"]
    assert revisao.versao == 2
    assert revisao.rotulo == "rascunho_revisao_v2"
    assert revisao.campos == ("titulo", "orientacao", "limite", "texto_atual", "contexto")
    assert revisao.limites_palavras["resumo_executivo"] == (150, 250)
    proposta = prompts["rascunho_proposta"]
    assert proposta.versao == 2
    assert set(proposta.alvos) == {"contexto", "objetivo_fase"}


def test_versao_1_continua_la_para_os_rascunhos_ja_gravados():
    for prompt_id in ("rascunho_revisao", "rascunho_proposta"):
        v1 = carregar_prompt(RAIZ / "prompts" / f"{prompt_id}_v1.md")
        assert v1.versao == 1
        assert v1.limites_palavras == {}
        assert "limite" not in v1.campos


def test_limites_cobrem_todos_os_textos(prompts, questionario_v1):
    revisao = prompts["rascunho_revisao"].limites_palavras
    assert {t.id for t in questionario_v1.revisao.textos} <= set(revisao)
    proposta = prompts["rascunho_proposta"]
    assert set(proposta.alvos) <= set(proposta.limites_palavras)
    for minimo, maximo in [*revisao.values(), *proposta.limites_palavras.values()]:
        assert 0 < minimo < maximo


def test_v2_trata_o_tamanho_como_limite(prompts):
    for prompt in prompts.values():
        assert "limite" in prompt.pedido
        assert "Respeite o tamanho pedido" in prompt.sistema


def test_descrever_limite(prompts):
    assert prompts["rascunho_revisao"].limite("resumo_executivo") == "entre 150 e 250 palavras"
    assert prompts["rascunho_revisao"].limite("nao_existe") is None


@pytest.mark.parametrize("prompt_id", ["rascunho_revisao", "rascunho_proposta"])
def test_regras_essenciais_no_sistema(prompts, prompt_id):
    sistema = prompts[prompt_id].sistema
    assert "Não faça contas" in sistema
    assert "marcadores" in sistema
    assert "[PESSOA_1]" in sistema
    assert "Não invente" in sistema


def test_preencher(tmp_path):
    prompt = carregar_prompt(_escrever(tmp_path, "teste_v2.md", VALIDO))
    assert prompt.rotulo == "teste_v2"
    pedido = prompt.preencher(nome="Ana")
    assert pedido.sistema == "Seja breve."
    assert pedido.mensagem == "Olá, Ana."


def test_valor_com_chaves_nao_e_preenchido_de_novo(tmp_path):
    prompt = carregar_prompt(_escrever(tmp_path, "teste_v2.md", VALIDO))
    assert prompt.preencher(nome="{{nome}}").mensagem == "Olá, {{nome}}."


@pytest.mark.parametrize(
    ("valores", "erro"),
    [({}, "falta o campo 'nome'"), ({"nome": "Ana", "extra": "x"}, "campo desconhecido")],
)
def test_preencher_exige_os_campos_declarados(tmp_path, valores, erro):
    prompt = carregar_prompt(_escrever(tmp_path, "teste_v2.md", VALIDO))
    with pytest.raises(ValueError, match=erro):
        prompt.preencher(**valores)


@pytest.mark.parametrize(
    ("nome", "texto", "erro"),
    [
        ("teste_v2.md", VALIDO.replace("---\nid", "id", 1), "cabeçalho"),
        ("teste_v3.md", VALIDO, "versão"),
        ("outro_v2.md", VALIDO, "id"),
        ("teste_v2.md", VALIDO.replace("# Sistema", "# Introdução"), "# Sistema"),
        ("teste_v2.md", VALIDO.replace("# Pedido", "# Mensagem"), "# Pedido"),
        ("teste_v2.md", VALIDO.replace("{{nome}}", "{{nome}} {{idade}}"), "idade"),
        ("teste_v2.md", VALIDO.replace("campos: [nome]", "campos: [nome, idade]"), "idade"),
        ("teste_v2.md", VALIDO.replace("versao: 2", "versao: dois"), "versao"),
        ("teste.md", VALIDO, "nome do arquivo"),
    ],
)
def test_arquivo_invalido(tmp_path, nome, texto, erro):
    with pytest.raises(PromptInvalido, match=erro):
        carregar_prompt(_escrever(tmp_path, nome, texto))


@pytest.mark.parametrize(
    "limites",
    [
        "limites_palavras: {nome: [250, 150]}",
        "limites_palavras: {nome: [0, 10]}",
        "limites_palavras: {nome: [10]}",
        "limites_palavras: {nome: muitas}",
    ],
)
def test_limites_invalidos(tmp_path, limites):
    texto = VALIDO.replace("campos: [nome]", f"campos: [nome]\n{limites}")
    with pytest.raises(PromptInvalido, match="limites_palavras"):
        carregar_prompt(_escrever(tmp_path, "teste_v2.md", texto))


def test_carregar_prompts_fica_com_a_versao_mais_recente(tmp_path):
    _escrever(tmp_path, "teste_v2.md", VALIDO)
    _escrever(tmp_path, "teste_v10.md", VALIDO.replace("versao: 2", "versao: 10"))
    _escrever(tmp_path, "LEIA-ME.txt", "não é prompt")
    _escrever(tmp_path, "LEIA-ME.md", "também não é prompt")
    assert carregar_prompts(tmp_path)["teste"].versao == 10

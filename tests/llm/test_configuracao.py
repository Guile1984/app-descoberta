"""Configuração do LLM (config/llm.yaml + variáveis de ambiente) e a chave de API."""

from pathlib import Path

import pytest
import yaml

from descoberta.llm.configuracao import (
    VARIAVEL_CHAVE,
    VARIAVEL_PROVEDOR,
    ConfiguracaoLLMInvalida,
    Provedor,
    carregar_configuracao_llm,
    ler_chave_api,
)

RAIZ = Path(__file__).resolve().parents[2]
# Chave falsa montada por partes: nenhum arquivo versionado pode conter o prefixo.
PREFIXO = "sk-" + "ant-"
CHAVE_FALSA = PREFIXO + "api03-SENTINELA-NUNCA-PODE-APARECER"


@pytest.fixture
def escrever(tmp_path):
    def escrever(dados) -> Path:
        caminho = tmp_path / "llm.yaml"
        caminho.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
        return caminho

    return escrever


def test_arquivo_do_projeto_vem_desligado_com_opus_5_5():
    config = carregar_configuracao_llm(RAIZ / "config" / "llm.yaml", ambiente={})
    assert config.provedor is Provedor.desligado
    assert config.claude.modelo == "claude-opus-5-5"
    assert config.claude.esforco == "medium"
    assert config.ollama.url == "http://localhost:11434"


def test_sem_arquivo_fica_desligado(tmp_path):
    config = carregar_configuracao_llm(tmp_path / "nao_existe.yaml", ambiente={})
    assert config.provedor is Provedor.desligado
    assert config.claude.modelo == "claude-opus-5-5"


@pytest.mark.parametrize("valor", ["claude", "ollama", "desligado", " Claude "])
def test_variavel_de_ambiente_escolhe_o_provedor(valor):
    config = carregar_configuracao_llm(
        RAIZ / "config" / "llm.yaml", ambiente={VARIAVEL_PROVEDOR: valor}
    )
    assert config.provedor == valor.strip().lower()


def test_variavel_em_branco_e_ignorada(escrever):
    caminho = escrever({"provedor": "ollama"})
    config = carregar_configuracao_llm(caminho, ambiente={VARIAVEL_PROVEDOR: "  "})
    assert config.provedor is Provedor.ollama


def test_variavel_com_provedor_desconhecido():
    with pytest.raises(ConfiguracaoLLMInvalida, match="DESCOBERTA_LLM_PROVEDOR") as erro:
        carregar_configuracao_llm(
            RAIZ / "config" / "llm.yaml", ambiente={VARIAVEL_PROVEDOR: "openai"}
        )
    assert "claude, ollama ou desligado" in str(erro.value)


@pytest.mark.parametrize(
    ("dados", "erro"),
    [
        ({"provedor": "gpt"}, "provedor"),
        ({"claude": {"esforco": "altissimo"}}, "esforco"),
        ({"claude": {"max_tokens": 10}}, "max_tokens"),
        ({"claude": {"tempo_limite_s": 0}}, "tempo_limite_s"),
        ({"claude": {"modelo": ""}}, "modelo"),
        ({"claude": {"chave": PREFIXO + "x"}}, "campo desconhecido"),
        ({"ollama": {"url": "http://192.168.0.10:11434"}}, "nesta máquina"),
        ({"ollama": {"url": "ftp://localhost:11434"}}, "http"),
        ({"outro": 1}, "campo desconhecido"),
    ],
)
def test_arquivo_invalido(escrever, dados, erro):
    with pytest.raises(ConfiguracaoLLMInvalida, match=erro):
        carregar_configuracao_llm(escrever(dados), ambiente={})


@pytest.mark.parametrize(
    "url", ["http://localhost:11434", "http://127.0.0.1:11434", "http://[::1]:11434"]
)
def test_ollama_so_nesta_maquina(escrever, url):
    config = carregar_configuracao_llm(escrever({"ollama": {"url": url}}), ambiente={})
    assert config.ollama.url == url


# --- Chave de API: só no ambiente, nunca exibida ---


def test_chave_vem_so_do_ambiente():
    assert ler_chave_api({}) is None
    assert ler_chave_api({VARIAVEL_CHAVE: "   "}) is None
    chave = ler_chave_api({VARIAVEL_CHAVE: f" {CHAVE_FALSA} "})
    assert chave.get_secret_value() == CHAVE_FALSA


def test_chave_nunca_aparece_ao_exibir():
    chave = ler_chave_api({VARIAVEL_CHAVE: CHAVE_FALSA})
    for texto in (str(chave), repr(chave), f"{chave}", f"{chave!r}"):
        assert CHAVE_FALSA not in texto
        assert PREFIXO not in texto


def test_configuracao_nao_guarda_a_chave():
    config = carregar_configuracao_llm(
        RAIZ / "config" / "llm.yaml",
        ambiente={VARIAVEL_PROVEDOR: "claude", VARIAVEL_CHAVE: CHAVE_FALSA},
    )
    assert CHAVE_FALSA not in repr(config)
    assert CHAVE_FALSA not in config.model_dump_json()


def test_arquivo_do_projeto_nao_tem_chave():
    texto = (RAIZ / "config" / "llm.yaml").read_text(encoding="utf-8")
    assert "sk-" not in texto
    assert "chave" not in yaml.safe_load(texto).get("claude", {})

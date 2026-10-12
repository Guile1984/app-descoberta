"""Configuração do LLM: config/llm.yaml, a variável DESCOBERTA_LLM_PROVEDOR e a chave.

A chave da API nunca fica na configuração: é lida do ambiente na hora de usar
(`ler_chave_api`) e volta como SecretStr, que aparece como '**********' ao ser exibida
(em log, mensagem de erro ou repr).
"""

import os
from collections.abc import Mapping
from enum import StrEnum
from ipaddress import ip_address
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator

from descoberta.questionario.carregador import ArquivoInvalido, carregar_yaml

VARIAVEL_PROVEDOR = "DESCOBERTA_LLM_PROVEDOR"
VARIAVEL_CHAVE = "ANTHROPIC_API_KEY"

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConfiguracaoLLMInvalida(ArquivoInvalido):
    """config/llm.yaml (ou a variável de ambiente) não passou na validação."""

    NOME = "Configuração do LLM"


class Provedor(StrEnum):
    desligado = "desligado"
    claude = "claude"
    ollama = "ollama"


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ConfigClaude(_Modelo):
    modelo: Texto = "claude-opus-5-5"
    esforco: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    max_tokens: int = Field(16000, ge=256, le=64000)
    tempo_limite_s: float = Field(60, gt=0)
    tentativas: int = Field(2, ge=0, le=5)


class ConfigOllama(_Modelo):
    url: Texto = "http://localhost:11434"
    modelo: Texto = "llama3.1:8b"
    tempo_limite_s: float = Field(180, gt=0)

    @field_validator("url")
    @classmethod
    def _so_nesta_maquina(cls, url: str) -> str:
        # O modelo local é a opção para quem não quer que nada saia da máquina: um Ollama
        # em outro computador da rede deixaria de ser "local".
        partes = urlsplit(url)
        if partes.scheme not in ("http", "https"):
            raise ValueError(f"use um endereço http://, como http://localhost:11434 ({url!r})")
        host = partes.hostname or ""
        try:
            local = host == "localhost" or ip_address(host).is_loopback
        except ValueError:
            local = False
        if not local:
            raise ValueError(f"o Ollama precisa rodar nesta máquina (localhost), não em {host!r}")
        return url.rstrip("/")


class ConfiguracaoLLM(_Modelo):
    provedor: Provedor = Provedor.desligado
    claude: ConfigClaude = ConfigClaude()
    ollama: ConfigOllama = ConfigOllama()


def carregar_configuracao_llm(
    caminho: Path | str, ambiente: Mapping[str, str] | None = None
) -> ConfiguracaoLLM:
    """Lê o arquivo (sem arquivo: tudo no padrão, desligado) e aplica DESCOBERTA_LLM_PROVEDOR."""
    caminho = Path(caminho)
    ambiente = os.environ if ambiente is None else ambiente
    if caminho.exists():
        config = carregar_yaml(caminho, ConfiguracaoLLM, ConfiguracaoLLMInvalida)
    else:
        config = ConfiguracaoLLM()
    escolhido = ambiente.get(VARIAVEL_PROVEDOR, "").strip().lower()
    if not escolhido:
        return config
    if escolhido not in {p.value for p in Provedor}:
        raise ConfiguracaoLLMInvalida(
            caminho,
            [f"{VARIAVEL_PROVEDOR}={escolhido!r} inválido; use claude, ollama ou desligado"],
        )
    return config.model_copy(update={"provedor": Provedor(escolhido)})


def ler_chave_api(ambiente: Mapping[str, str] | None = None) -> SecretStr | None:
    """A chave da API da Anthropic, só do ambiente; None se não estiver definida."""
    ambiente = os.environ if ambiente is None else ambiente
    chave = ambiente.get(VARIAVEL_CHAVE, "").strip()
    return SecretStr(chave) if chave else None

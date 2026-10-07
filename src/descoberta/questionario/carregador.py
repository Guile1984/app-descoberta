"""Leitura do arquivo YAML do questionário, com mensagens de erro em português."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .modelos import Questionario


class QuestionarioInvalido(Exception):
    """O arquivo do questionário não pôde ser lido ou não passou na validação."""

    def __init__(self, caminho: Path, erros: list[str]):
        self.caminho = caminho
        self.erros = erros
        linhas = "\n".join(f"  - {erro}" for erro in erros)
        super().__init__(f"Questionário inválido ({caminho.name}):\n{linhas}")


def carregar_questionario(caminho: Path | str) -> Questionario:
    caminho = Path(caminho)
    dados = _ler_yaml(caminho)
    try:
        return Questionario.model_validate(dados)
    except ValidationError as erro:
        raise QuestionarioInvalido(
            caminho, [_descrever_erro(detalhe, dados) for detalhe in erro.errors()]
        ) from erro


def _ler_yaml(caminho: Path) -> dict:
    try:
        texto = caminho.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise QuestionarioInvalido(caminho, [f"arquivo não encontrado: {caminho}"]) from None
    try:
        # safe_load só monta tipos simples (texto, número, lista, dicionário): nunca executa
        # código vindo do arquivo.
        dados = yaml.safe_load(texto)
    except yaml.YAMLError as erro:
        raise QuestionarioInvalido(caminho, [_descrever_erro_yaml(erro)]) from erro
    if dados is None:
        raise QuestionarioInvalido(caminho, ["o arquivo está vazio"])
    if not isinstance(dados, dict):
        raise QuestionarioInvalido(
            caminho, ["a raiz do arquivo deve ser um mapeamento (chave: valor)"]
        )
    return dados


def _descrever_erro_yaml(erro: yaml.YAMLError) -> str:
    marca = getattr(erro, "problem_mark", None)
    problema = getattr(erro, "problem", None) or str(erro)
    if marca is None:
        return f"YAML mal formado: {problema}"
    # O PyYAML conta linhas e colunas a partir de 0; editores contam a partir de 1.
    return f"YAML mal formado na linha {marca.line + 1}, coluna {marca.column + 1}: {problema}"


def _descrever_erro(detalhe: dict, dados: Any) -> str:
    local = _formatar_local(detalhe["loc"], dados)
    mensagem = _traduzir(detalhe)
    return f"{local}: {mensagem}" if local else mensagem


def _formatar_local(loc: tuple, dados: Any) -> str:
    """Transforma o caminho do erro do Pydantic em texto legível.

    Ex.: ("blocos", 1, "perguntas", 0, "tipo") → blocos[id=bloco_2].perguntas[id=b2.o1].tipo.
    Itens de lista aparecem pelo id quando têm um; senão pela posição, contando de 1.
    """
    partes: list[str] = []
    atual = dados
    for chave in loc:
        if isinstance(chave, int):
            item = atual[chave] if isinstance(atual, list) and chave < len(atual) else None
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                partes.append(f"[id={item['id']}]")
            else:
                partes.append(f"[nº {chave + 1}]")
            atual = item
        else:
            partes.append(f".{chave}" if partes else chave)
            atual = atual.get(chave) if isinstance(atual, dict) else None
    return "".join(partes)


def _traduzir(detalhe: dict) -> str:
    tipo = detalhe["type"]
    if tipo == "missing":
        return "campo obrigatório ausente"
    if tipo == "extra_forbidden":
        return "campo desconhecido (verifique a grafia)"
    if tipo == "literal_error":
        aceitos = detalhe["ctx"]["expected"].replace(" or ", " ou ")
        return f"valor {detalhe['input']!r} inválido; use {aceitos}"
    if tipo in {"value_error", "assertion_error"}:
        return str(detalhe["ctx"]["error"])
    if tipo == "too_short":
        return "a lista não pode ficar vazia"
    if tipo == "string_too_short":
        return "o texto não pode ficar vazio"
    if tipo == "string_pattern_mismatch":
        return (
            f"id {detalhe['input']!r} inválido; use só letras minúsculas sem acento, "
            "números, '_' e '.'"
        )
    if tipo == "string_type":
        return f"esperava um texto, recebeu {detalhe['input']!r}"
    if tipo in {"int_type", "int_parsing"}:
        return f"esperava um número inteiro, recebeu {detalhe['input']!r}"
    if tipo == "greater_than_equal":
        return f"o valor deve ser no mínimo {detalhe['ctx']['ge']}, recebeu {detalhe['input']!r}"
    if tipo in {"list_type", "dict_type", "model_type"}:
        esperado = "uma lista" if tipo == "list_type" else "um mapeamento (chave: valor)"
        return f"esperava {esperado}, recebeu {detalhe['input']!r}"
    return f"{detalhe['msg']} (valor recebido: {detalhe['input']!r})"

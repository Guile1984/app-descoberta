"""Resolve quais perguntas aparecem, de acordo com o tipo de solução escolhido no bloco 3."""

from .modelos import Pergunta, Questionario


def _exigir_tipo(questionario: Questionario, tipo_solucao: str | None) -> None:
    tipos_existentes = {tipo.id for tipo in questionario.tipos_solucao}
    if tipo_solucao is not None and tipo_solucao not in tipos_existentes:
        raise ValueError(f"tipo de solução inexistente no questionário: '{tipo_solucao}'")


def _aparece(pergunta: Pergunta, tipo_solucao: str | None) -> bool:
    return pergunta.condicao is None or tipo_solucao in pergunta.condicao.tipos_solucao


def perguntas_visiveis(
    questionario: Questionario, numero_bloco: int, tipo_solucao: str | None
) -> list[Pergunta]:
    """Perguntas do bloco a exibir, na ordem do YAML.

    Perguntas sem condição sempre aparecem. As condicionais só aparecem quando o tipo de
    solução da sessão está na condição; sem tipo definido (bloco 3 ainda em aberto),
    nenhuma condicional aparece.
    """
    _exigir_tipo(questionario, tipo_solucao)
    return [
        pergunta
        for pergunta in questionario.bloco(numero_bloco).perguntas
        if _aparece(pergunta, tipo_solucao)
    ]


def pergunta_visivel(
    questionario: Questionario, pergunta_id: str, tipo_solucao: str | None
) -> bool:
    """Se a pergunta aparece para esse tipo de solução (KeyError se ela não existe)."""
    _exigir_tipo(questionario, tipo_solucao)
    _, pergunta = questionario.pergunta(pergunta_id)
    return _aparece(pergunta, tipo_solucao)

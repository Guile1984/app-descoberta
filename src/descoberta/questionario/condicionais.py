"""Resolve quais perguntas aparecem, de acordo com o tipo de solução escolhido no bloco 3."""

from .modelos import Pergunta, Questionario


def perguntas_visiveis(
    questionario: Questionario, numero_bloco: int, tipo_solucao: str | None
) -> list[Pergunta]:
    """Perguntas do bloco a exibir, na ordem do YAML.

    Perguntas sem condição sempre aparecem. As condicionais só aparecem quando o tipo de
    solução da sessão está na condição; sem tipo definido (bloco 3 ainda em aberto),
    nenhuma condicional aparece.
    """
    tipos_existentes = {tipo.id for tipo in questionario.tipos_solucao}
    if tipo_solucao is not None and tipo_solucao not in tipos_existentes:
        raise ValueError(f"tipo de solução inexistente no questionário: '{tipo_solucao}'")
    return [
        pergunta
        for pergunta in questionario.bloco(numero_bloco).perguntas
        if pergunta.condicao is None or tipo_solucao in pergunta.condicao.tipos_solucao
    ]

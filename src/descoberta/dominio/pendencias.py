"""Perguntas obrigatórias ainda sem resposta, para o indicador da sessão ao vivo."""

from collections.abc import Iterable

from descoberta.questionario import Questionario, perguntas_visiveis


def obrigatorias_pendentes(
    questionario: Questionario, tipo_solucao: str | None, respondidas: Iterable[str]
) -> dict[int, list[str]]:
    """Ids das obrigatórias visíveis e sem resposta, por bloco (todos os blocos aparecem).

    Condicionais escondidas pelo tipo de solução atual não contam, nem como pendentes nem
    como respondidas.
    """
    respondidas = set(respondidas)
    return {
        bloco.numero: [
            pergunta.id
            for pergunta in perguntas_visiveis(questionario, bloco.numero, tipo_solucao)
            if pergunta.tipo == "obrigatoria" and pergunta.id not in respondidas
        ]
        for bloco in questionario.blocos
    }

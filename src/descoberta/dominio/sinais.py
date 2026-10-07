"""Sinais de alerta marcados durante a sessão."""

from collections.abc import Iterable

from descoberta.questionario import Questionario


def contar_sinais_por_bloco(
    questionario: Questionario, ids_marcados: Iterable[str]
) -> dict[int, int]:
    """Quantos sinais foram marcados em cada bloco; todos os blocos aparecem, mesmo com 0.

    Um id repetido conta uma vez. Um id que não existe no questionário gera erro, para que
    um sinal gravado com id errado não suma da contagem sem aviso.
    """
    bloco_do_sinal = {
        sinal.id: bloco.numero for bloco in questionario.blocos for sinal in bloco.sinais
    }
    marcados = set(ids_marcados)
    desconhecidos = sorted(marcados - bloco_do_sinal.keys())
    if desconhecidos:
        lista = ", ".join(f"'{id_}'" for id_ in desconhecidos)
        raise ValueError(f"sinal de alerta inexistente no questionário: {lista}")
    contagem = dict.fromkeys((bloco.numero for bloco in questionario.blocos), 0)
    for id_ in marcados:
        contagem[bloco_do_sinal[id_]] += 1
    return contagem

"""Tudo o que as telas da sessão ao vivo mostram, lido do banco e calculado pelo domínio.

Cada pedaço da tela (painel do bloco, abas, cálculos, pendências…) usa o mesmo contexto.
O banco é pequeno (uma sessão tem dezenas de registros), então ler tudo a cada pedido
é simples e rápido, e não há risco de um pedaço mostrar dados diferentes de outro.
"""

from dataclasses import fields
from typing import Any

from sqlmodel import Session

from descoberta.dominio.painel import EntradasPainel, Painel, calcular_painel
from descoberta.dominio.pendencias import obrigatorias_pendentes
from descoberta.questionario import Questionario, perguntas_visiveis
from descoberta.repositorio import (
    Metricas,
    Sessao,
    anotacoes_da_sessao,
    notas_da_sessao,
    obter_metricas,
    respostas_da_sessao,
    sinais_marcados,
)

from .campos import CAMPO_POR_NOME, PERIODOS, campos_do_bloco


def entradas_do_painel(metricas: Metricas | None) -> EntradasPainel:
    """As métricas gravadas, campo a campo (os nomes são os mesmos)."""
    if metricas is None:
        return EntradasPainel()
    return EntradasPainel(**{c.name: getattr(metricas, c.name) for c in fields(EntradasPainel)})


def _rotulos(questionario: Questionario) -> dict[str, str]:
    """Nome de campo ou critério → rótulo, para dizer o que falta em cada cálculo."""
    scores = questionario.scores
    criterios = [*scores.prontidao_dados.criterios, *scores.viabilidade_final.criterios]
    return {campo.nome: campo.rotulo for campo in CAMPO_POR_NOME.values()} | {
        criterio.id: criterio.rotulo for criterio in criterios
    }


def contexto_da_sessao(banco: Session, sessao: Sessao, questionario: Questionario) -> dict:
    respostas = respostas_da_sessao(banco, sessao.id)
    metricas = obter_metricas(banco, sessao.id)
    notas = notas_da_sessao(banco, sessao.id)
    marcados = {sinal.sinal_id: sinal for sinal in sinais_marcados(banco, sessao.id)}
    painel: Painel | None = None
    erro_calculo: str | None = None
    try:
        painel = calcular_painel(entradas_do_painel(metricas), notas, marcados, questionario)
    except ValueError as erro:
        # Dado gravado que o questionário da sessão não reconhece: a tela continua de pé.
        erro_calculo = str(erro)
    pendentes = obrigatorias_pendentes(questionario, sessao.tipo_solucao, respostas)
    return {
        "sessao": sessao,
        "questionario": questionario,
        "respostas": respostas,
        "metricas": metricas,
        "notas": notas,
        "marcados": marcados,
        "anotacoes": list(reversed(anotacoes_da_sessao(banco, sessao.id))),
        "painel": painel,
        "erro_calculo": erro_calculo,
        "pendentes": pendentes,
        "total_pendentes": sum(len(ids) for ids in pendentes.values()),
        "rotulos": _rotulos(questionario),
        "periodos": PERIODOS,
        "campos_do_bloco": campos_do_bloco,
    }


def contexto_da_aba(contexto: dict[str, Any], aba: int | str) -> dict[str, Any]:
    """Acrescenta a aba aberta: o número do bloco ou "encerramento"."""
    questionario: Questionario = contexto["questionario"]
    if not isinstance(aba, int):
        return contexto | {"aba": aba, "bloco": None}
    perguntas = perguntas_visiveis(questionario, aba, contexto["sessao"].tipo_solucao)
    return contexto | {
        "aba": aba,
        "bloco": questionario.bloco(aba),
        "obrigatorias": [p for p in perguntas if p.tipo == "obrigatoria"],
        "aprofundamento": [p for p in perguntas if p.tipo == "aprofundamento"],
    }

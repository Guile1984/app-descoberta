"""Painel de cálculos ao vivo: aplica os cálculos do domínio ao que já foi levantado.

Durante a conversa quase tudo começa vazio. Este módulo não faz conta nenhuma por conta
própria: chama as funções de `dor`, `operacao`, `payback`, `scores` e `sinais` quando as
entradas de cada uma existem e, quando não existem, diz quais faltam. O relatório
(Sprint 6) usa o mesmo painel.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from descoberta.questionario import Questionario

from .dor import custo_dor_mes, horas_dor_mes, ocorrencias_por_mes
from .operacao import custo_operacao_mes
from .payback import economia_mes, payback_dificil_de_aprovar, payback_meses
from .scores import (
    ScoreParcial,
    nota_prontidao_para_viabilidade,
    score_prontidao_parcial,
    score_viabilidade_parcial,
)
from .sinais import contar_sinais_por_bloco
from .valores import Numero


@dataclass(frozen=True)
class EntradasPainel:
    """Números levantados na sessão; os nomes são os mesmos campos da tabela Metricas."""

    horas_por_ocorrencia: Numero | None = None
    frequencia_quantidade: Numero | None = None
    frequencia_periodo: str | None = None
    custo_hora: Numero | None = None
    horas_economizadas_mes: Numero | None = None
    outros_ganhos_mes: Numero | None = None
    investimento: Numero | None = None
    chamadas_por_dia: Numero | None = None
    custo_por_chamada: Numero | None = None
    custo_fixo_mes: Numero | None = None


@dataclass(frozen=True)
class Calculo:
    """Resultado de um cálculo, ou None com os nomes das entradas que faltam."""

    valor: Decimal | None
    faltando: tuple[str, ...] = ()


@dataclass(frozen=True)
class Payback:
    meses: Decimal | None
    faltando: tuple[str, ...]
    nunca_se_paga: bool  # economia não supera a operação (com todos os dados)
    dificil_de_aprovar: bool | None  # None enquanto falta dado


@dataclass(frozen=True)
class Painel:
    ocorrencias_mes: Calculo
    horas_dor_mes: Calculo
    custo_dor_mes: Calculo
    operacao_mes: Calculo
    economia_mes: Calculo
    payback: Payback
    score_dados: ScoreParcial
    nota_prontidao: int | None  # nota derivada do score de dados para o score final
    score_final: ScoreParcial
    sinais_por_bloco: dict[int, int]


def _sem_repetir(*grupos: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(nome for grupo in grupos for nome in grupo))


def _vazios(**entradas: object) -> tuple[str, ...]:
    return tuple(nome for nome, valor in entradas.items() if valor is None)


def _se_completo(faltando: tuple[str, ...], conta: Callable[[], Decimal]) -> Calculo:
    """Faz a conta só quando nada falta; senão guarda o que falta."""
    return Calculo(None, faltando) if faltando else Calculo(conta())


def _operacao(e: EntradasPainel) -> Calculo:
    # Sem nenhum dos três, falta tudo. Com parte variável, precisa das duas metades;
    # o que não foi informado (só custo fixo, ou só a parte variável) entra como zero.
    variavel = {"chamadas_por_dia": e.chamadas_por_dia, "custo_por_chamada": e.custo_por_chamada}
    if e.custo_fixo_mes is None and all(v is None for v in variavel.values()):
        return Calculo(None, (*variavel, "custo_fixo_mes"))
    if any(v is None for v in variavel.values()) and any(v is not None for v in variavel.values()):
        return Calculo(None, tuple(nome for nome, v in variavel.items() if v is None))
    return Calculo(
        custo_operacao_mes(
            chamadas_por_dia=e.chamadas_por_dia or 0,
            custo_por_chamada=e.custo_por_chamada or 0,
            custo_fixo_mes=e.custo_fixo_mes or 0,
        )
    )


def _payback(e: EntradasPainel, economia: Calculo, operacao: Calculo) -> Payback:
    faltando = _sem_repetir(
        _vazios(investimento=e.investimento), economia.faltando, operacao.faltando
    )
    if faltando:
        return Payback(None, faltando, nunca_se_paga=False, dificil_de_aprovar=None)
    meses = payback_meses(e.investimento, economia.valor, operacao.valor)
    return Payback(
        meses,
        (),
        nunca_se_paga=meses is None,
        dificil_de_aprovar=payback_dificil_de_aprovar(meses),
    )


def _separar_notas(
    notas: Mapping[str, int], questionario: Questionario
) -> tuple[dict[str, int], dict[str, int]]:
    """Divide as notas da sessão entre o score de dados e o score final."""
    dados = questionario.scores.prontidao_dados
    ids_dados = {c.id for c in dados.criterios}
    if dados.criterio_final in notas:
        raise ValueError(
            f"a nota de '{dados.criterio_final}' sai do score de dados e não pode ser dada à mão"
        )
    notas_dados = {c: n for c, n in notas.items() if c in ids_dados}
    notas_finais = {c: n for c, n in notas.items() if c not in ids_dados}
    return notas_dados, notas_finais


def calcular_painel(
    entradas: EntradasPainel,
    notas: Mapping[str, int],
    sinais_marcados: Iterable[str],
    questionario: Questionario,
) -> Painel:
    e = entradas
    ocorrencias = _se_completo(
        _vazios(
            frequencia_quantidade=e.frequencia_quantidade, frequencia_periodo=e.frequencia_periodo
        ),
        lambda: ocorrencias_por_mes(e.frequencia_quantidade, e.frequencia_periodo),
    )
    horas = _se_completo(
        _sem_repetir(_vazios(horas_por_ocorrencia=e.horas_por_ocorrencia), ocorrencias.faltando),
        lambda: horas_dor_mes(e.horas_por_ocorrencia, ocorrencias.valor),
    )
    custo = _se_completo(
        _sem_repetir(horas.faltando, _vazios(custo_hora=e.custo_hora)),
        lambda: custo_dor_mes(horas.valor, e.custo_hora),
    )
    operacao = _operacao(e)
    economia = _se_completo(
        _vazios(horas_economizadas_mes=e.horas_economizadas_mes, custo_hora=e.custo_hora),
        lambda: economia_mes(e.horas_economizadas_mes, e.custo_hora, e.outros_ganhos_mes or 0),
    )

    notas_dados, notas_finais = _separar_notas(notas, questionario)
    score_dados = score_prontidao_parcial(notas_dados, questionario)
    nota_prontidao = None
    if score_dados.resultado is not None:
        nota_prontidao = nota_prontidao_para_viabilidade(score_dados.pontuacao, questionario)
        notas_finais[questionario.scores.prontidao_dados.criterio_final] = nota_prontidao

    return Painel(
        ocorrencias_mes=ocorrencias,
        horas_dor_mes=horas,
        custo_dor_mes=custo,
        operacao_mes=operacao,
        economia_mes=economia,
        payback=_payback(e, economia, operacao),
        score_dados=score_dados,
        nota_prontidao=nota_prontidao,
        score_final=score_viabilidade_parcial(notas_finais, questionario),
        sinais_por_bloco=contar_sinais_por_bloco(questionario, sinais_marcados),
    )

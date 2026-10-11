"""Métricas numéricas da sessão e notas dos critérios dos scores."""

from typing import Any, get_args

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from descoberta.dominio.dor import Periodo

from ._comum import (
    aplicar_campos,
    decimal_opcional,
    exigir_sessao,
    gravar,
    id_questionario,
    nota,
)
from .modelos import HipoteseMetrica, Metricas, NotaCriterio


def _periodo(nome: str, valor: Any) -> str | None:
    # Os períodos aceitos são os mesmos que o cálculo do custo da dor entende.
    aceitos = get_args(Periodo)
    if valor is not None and valor not in aceitos:
        lista = ", ".join(f"'{periodo}'" for periodo in aceitos)
        raise ValueError(f"{nome} {valor!r} inválido; use {lista}")
    return valor


_VALIDADORES = {
    "horas_por_ocorrencia": decimal_opcional,
    "frequencia_quantidade": decimal_opcional,
    "frequencia_periodo": _periodo,
    "custo_hora": decimal_opcional,
    "horas_economizadas_mes": decimal_opcional,
    "outros_ganhos_mes": decimal_opcional,
    "investimento": decimal_opcional,
    "chamadas_por_dia": decimal_opcional,
    "custo_por_chamada": decimal_opcional,
    "custo_fixo_mes": decimal_opcional,
}


def salvar_metricas(session: Session, sessao_id: int, **campos: Any) -> Metricas:
    """Grava só os campos informados; os outros ficam como estavam.

    Dinheiro, horas e quantidades aceitam int ou Decimal (float é recusado) e são
    guardados como Decimal. None apaga o valor do campo.
    """
    exigir_sessao(session, sessao_id)
    try:
        return _gravar_metricas(session, sessao_id, campos)
    except IntegrityError:
        # Todas as métricas ficam numa linha só. Numa sessão nova, dois números salvos
        # quase juntos chegam em pedidos paralelos: os dois veem que a linha não existe e
        # tentam criá-la, e o segundo esbarra no primeiro. Desfaz e grava de novo, agora
        # atualizando a linha que o outro pedido criou.
        session.rollback()
        return _gravar_metricas(session, sessao_id, campos)


def _gravar_metricas(session: Session, sessao_id: int, campos: dict[str, Any]) -> Metricas:
    metricas = session.get(Metricas, sessao_id) or Metricas(sessao_id=sessao_id)
    aplicar_campos(metricas, campos, _VALIDADORES)
    return gravar(session, metricas)


def obter_metricas(session: Session, sessao_id: int) -> Metricas | None:
    return session.get(Metricas, sessao_id)


def salvar_nota(
    session: Session, sessao_id: int, criterio_id: str, valor: int | None
) -> NotaCriterio | None:
    """Grava a nota (0–3) de um critério de score; None apaga a nota."""
    criterio_id = id_questionario("criterio_id", criterio_id)
    if valor is not None:
        valor = nota("nota", valor)
    exigir_sessao(session, sessao_id)
    registro = session.exec(
        select(NotaCriterio).where(
            NotaCriterio.sessao_id == sessao_id, NotaCriterio.criterio_id == criterio_id
        )
    ).first()
    if valor is None:
        if registro is not None:
            session.delete(registro)
            session.commit()
        return None
    if registro is None:
        registro = NotaCriterio(sessao_id=sessao_id, criterio_id=criterio_id, nota=valor)
    else:
        registro.nota = valor
    return gravar(session, registro)


def notas_da_sessao(session: Session, sessao_id: int) -> dict[str, int]:
    """Notas da sessão: id do critério → nota (dos dois scores, juntos)."""
    registros = session.exec(select(NotaCriterio).where(NotaCriterio.sessao_id == sessao_id))
    return {registro.criterio_id: registro.nota for registro in registros}


# --- Hipóteses ---

# Só os números podem ser hipótese (o período da frequência é uma escolha, não um valor).
CAMPOS_NUMERICOS = tuple(
    nome for nome, validar in _VALIDADORES.items() if validar is decimal_opcional
)


def marcar_hipotese(session: Session, sessao_id: int, campo: str, hipotese: bool) -> None:
    """Marca (ou desmarca) uma métrica como hipótese do consultor; repetir não duplica."""
    if campo not in CAMPOS_NUMERICOS:
        raise ValueError(f"campo '{campo}' não é uma métrica numérica")
    exigir_sessao(session, sessao_id)
    registro = session.exec(
        select(HipoteseMetrica).where(
            HipoteseMetrica.sessao_id == sessao_id, HipoteseMetrica.campo == campo
        )
    ).first()
    if hipotese and registro is None:
        gravar(session, HipoteseMetrica(sessao_id=sessao_id, campo=campo))
    elif not hipotese and registro is not None:
        session.delete(registro)
        session.commit()


def hipoteses_da_sessao(session: Session, sessao_id: int) -> set[str]:
    consulta = select(HipoteseMetrica.campo).where(HipoteseMetrica.sessao_id == sessao_id)
    return set(session.exec(consulta.order_by(col(HipoteseMetrica.id))))

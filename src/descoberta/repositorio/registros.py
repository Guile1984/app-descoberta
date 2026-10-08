"""O que o consultor registra durante a sessão: respostas, sinais de alerta e anotações."""

from sqlmodel import Session, col, select

from ._comum import (
    RegistroNaoEncontrado,
    exigir,
    exigir_sessao,
    gravar,
    id_questionario,
    inteiro_opcional,
    texto_obrigatorio,
    texto_opcional,
)
from .modelos import Anotacao, Resposta, SinalMarcado, agora

# --- Respostas ---


def salvar_resposta(
    session: Session, sessao_id: int, pergunta_id: str, texto: str
) -> Resposta | None:
    """Cria ou atualiza a resposta de uma pergunta (uma por pergunta em cada sessão).

    Pensado para o salvamento automático: apagar todo o texto do campo apaga a resposta,
    e a função devolve None. O texto é guardado exatamente como foi digitado.
    """
    pergunta_id = id_questionario("pergunta_id", pergunta_id)
    if not isinstance(texto, str):
        raise TypeError(f"texto precisa ser texto (recebido {texto!r})")
    exigir_sessao(session, sessao_id)
    resposta = session.exec(
        select(Resposta).where(Resposta.sessao_id == sessao_id, Resposta.pergunta_id == pergunta_id)
    ).first()
    if not texto.strip():
        if resposta is not None:
            session.delete(resposta)
            session.commit()
        return None
    if resposta is None:
        resposta = Resposta(sessao_id=sessao_id, pergunta_id=pergunta_id, texto=texto)
    else:
        resposta.texto = texto
        resposta.atualizado_em = agora()
    return gravar(session, resposta)


def respostas_da_sessao(session: Session, sessao_id: int) -> dict[str, str]:
    """Respostas da sessão: id da pergunta → texto."""
    respostas = session.exec(select(Resposta).where(Resposta.sessao_id == sessao_id))
    return {resposta.pergunta_id: resposta.texto for resposta in respostas}


# --- Sinais de alerta ---


def _sinal(session: Session, sessao_id: int, sinal_id: str) -> SinalMarcado | None:
    return session.exec(
        select(SinalMarcado).where(
            SinalMarcado.sessao_id == sessao_id, SinalMarcado.sinal_id == sinal_id
        )
    ).first()


def marcar_sinal(
    session: Session, sessao_id: int, sinal_id: str, observacao: str | None = None
) -> SinalMarcado:
    """Marca o sinal; marcar de novo não duplica (só atualiza a observação, se vier uma)."""
    sinal_id = id_questionario("sinal_id", sinal_id)
    observacao = texto_opcional("observacao", observacao)
    exigir_sessao(session, sessao_id)
    sinal = _sinal(session, sessao_id, sinal_id)
    if sinal is None:
        sinal = SinalMarcado(sessao_id=sessao_id, sinal_id=sinal_id, observacao=observacao)
    elif observacao is not None:
        sinal.observacao = observacao
    return gravar(session, sinal)


def anotar_sinal(session: Session, sessao_id: int, sinal_id: str, observacao: str | None):
    """Troca a observação de um sinal já marcado; texto em branco apaga a observação."""
    sinal = _sinal(session, sessao_id, id_questionario("sinal_id", sinal_id))
    if sinal is None:
        raise RegistroNaoEncontrado(f"sinal {sinal_id} não está marcado na sessão {sessao_id}")
    sinal.observacao = texto_opcional("observacao", observacao)
    return gravar(session, sinal)


def desmarcar_sinal(session: Session, sessao_id: int, sinal_id: str) -> None:
    sinal = _sinal(session, sessao_id, sinal_id)
    if sinal is not None:
        session.delete(sinal)
        session.commit()


def sinais_marcados(session: Session, sessao_id: int) -> list[SinalMarcado]:
    """Sinais marcados na sessão, na ordem em que foram marcados."""
    consulta = (
        select(SinalMarcado)
        .where(SinalMarcado.sessao_id == sessao_id)
        .order_by(col(SinalMarcado.marcado_em), col(SinalMarcado.id))
    )
    return list(session.exec(consulta))


# --- Anotações livres ---


def adicionar_anotacao(
    session: Session, sessao_id: int, texto: str, bloco: int | None = None
) -> Anotacao:
    """Anotação livre; `bloco` liga a anotação a um bloco do questionário (opcional)."""
    texto = texto_obrigatorio("texto", texto)
    bloco = inteiro_opcional("bloco", bloco, minimo=1)
    exigir_sessao(session, sessao_id)
    return gravar(session, Anotacao(sessao_id=sessao_id, bloco=bloco, texto=texto))


def editar_anotacao(session: Session, anotacao_id: int, texto: str) -> Anotacao:
    anotacao = exigir(session, Anotacao, anotacao_id, "anotação")
    anotacao.texto = texto_obrigatorio("texto", texto)
    return gravar(session, anotacao)


def excluir_anotacao(session: Session, anotacao_id: int) -> None:
    session.delete(exigir(session, Anotacao, anotacao_id, "anotação"))
    session.commit()


def anotacoes_da_sessao(session: Session, sessao_id: int) -> list[Anotacao]:
    """Anotações da sessão, da mais antiga para a mais recente."""
    consulta = (
        select(Anotacao)
        .where(Anotacao.sessao_id == sessao_id)
        .order_by(col(Anotacao.criado_em), col(Anotacao.id))
    )
    return list(session.exec(consulta))

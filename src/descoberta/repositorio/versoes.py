"""Versões registradas como enviadas: do relatório e da proposta, cada um com a sua
numeração.

O PDF fica guardado exatamente como foi emitido: baixar a versão 3 amanhã devolve o mesmo
arquivo, mesmo que os dados da sessão tenham mudado depois.
"""

import hashlib
from datetime import datetime
from typing import Any

from sqlmodel import Session, col, func, select

from ._comum import exigir_sessao, gravar, inteiro, opcao
from .modelos import TipoVersao, VersaoProposta, VersaoRelatorio


def sha256(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def hash_do_conteudo(conteudo_md: str) -> str:
    """O hash impresso no rodapé: SHA-256 do texto do relatório (UTF-8)."""
    return sha256(conteudo_md.encode("utf-8"))


def _conteudo(nome: str, valor: Any) -> str:
    # Sem aparar espaços: o hash precisa ser do texto exatamente como foi emitido.
    if not isinstance(valor, str):
        raise TypeError(f"{nome} precisa ser texto (recebido {type(valor).__name__})")
    if not valor.strip():
        raise ValueError(f"{nome} não pode ficar vazio")
    return valor


def _pdf(nome: str, valor: Any) -> bytes:
    if not isinstance(valor, bytes):
        raise TypeError(f"{nome} precisa ser o arquivo em bytes (recebido {type(valor).__name__})")
    if not valor:
        raise ValueError(f"{nome} está vazio")
    return valor


def _momento(nome: str, valor: Any) -> datetime:
    if not isinstance(valor, datetime) or valor.tzinfo is None:
        raise TypeError(f"{nome} precisa ser data e hora com fuso (recebido {valor!r})")
    return valor


def _proximo_numero(session: Session, modelo, sessao_id: int) -> int:
    maior = session.exec(select(func.max(modelo.numero)).where(modelo.sessao_id == sessao_id)).one()
    return (maior or 0) + 1


def _gravar_versao(session: Session, versao):
    try:
        return gravar(session, versao)
    except Exception:
        session.rollback()  # a sessão do banco continua usável depois do erro
        raise


def proximo_numero_versao(session: Session, sessao_id: int) -> int:
    return _proximo_numero(session, VersaoRelatorio, sessao_id)


def registrar_versao(
    session: Session,
    sessao_id: int,
    *,
    numero: int,
    tipo: TipoVersao | str,
    emitido_em: datetime,
    conteudo_md: str,
    pdf: bytes,
) -> VersaoRelatorio:
    """Guarda o PDF emitido; os dois hashes são calculados aqui, a partir do que é gravado.

    Número repetido na mesma sessão é recusado pelo banco (UniqueConstraint).
    """
    numero = inteiro("numero", numero, minimo=1)
    tipo = opcao(TipoVersao)("tipo", tipo)
    emitido_em = _momento("emitido_em", emitido_em)
    conteudo_md = _conteudo("conteudo_md", conteudo_md)
    pdf = _pdf("pdf", pdf)
    exigir_sessao(session, sessao_id)
    versao = VersaoRelatorio(
        sessao_id=sessao_id,
        numero=numero,
        tipo=tipo,
        emitido_em=emitido_em,
        conteudo_md=conteudo_md,
        hash_conteudo=hash_do_conteudo(conteudo_md),
        pdf=pdf,
        hash_pdf=sha256(pdf),
    )
    return _gravar_versao(session, versao)


def versoes_da_sessao(session: Session, sessao_id: int) -> list[VersaoRelatorio]:
    """Versões registradas, da mais recente para a mais antiga."""
    consulta = (
        select(VersaoRelatorio)
        .where(VersaoRelatorio.sessao_id == sessao_id)
        .order_by(col(VersaoRelatorio.numero).desc())
    )
    return list(session.exec(consulta))


def obter_versao(session: Session, sessao_id: int, numero: int) -> VersaoRelatorio | None:
    return session.exec(
        select(VersaoRelatorio).where(
            VersaoRelatorio.sessao_id == sessao_id, VersaoRelatorio.numero == numero
        )
    ).first()


# --- Proposta ---


def _clausulas(nome: str, valor: Any) -> list[dict[str, str]]:
    if not isinstance(valor, list) or not all(
        isinstance(c, dict) and {"id", "titulo", "texto"} <= c.keys() for c in valor
    ):
        raise ValueError(f"{nome} precisa ser uma lista de cláusulas com id, titulo e texto")
    return [{"id": c["id"], "titulo": c["titulo"], "texto": c["texto"]} for c in valor]


def proximo_numero_versao_proposta(session: Session, sessao_id: int) -> int:
    return _proximo_numero(session, VersaoProposta, sessao_id)


def registrar_versao_proposta(
    session: Session,
    sessao_id: int,
    *,
    numero: int,
    emitido_em: datetime,
    conteudo_md: str,
    pdf: bytes,
    versao_modelo: int,
    clausulas: list[dict[str, str]],
) -> VersaoProposta:
    """Guarda o PDF da proposta, os hashes e as Condições Gerais como foram emitidas."""
    versao = VersaoProposta(
        sessao_id=sessao_id,
        numero=inteiro("numero", numero, minimo=1),
        emitido_em=_momento("emitido_em", emitido_em),
        conteudo_md=_conteudo("conteudo_md", conteudo_md),
        hash_conteudo=hash_do_conteudo(conteudo_md),
        pdf=_pdf("pdf", pdf),
        hash_pdf=sha256(pdf),
        versao_modelo=inteiro("versao_modelo", versao_modelo, minimo=1),
        clausulas=_clausulas("clausulas", clausulas),
    )
    exigir_sessao(session, sessao_id)
    return _gravar_versao(session, versao)


def versoes_da_proposta(session: Session, sessao_id: int) -> list[VersaoProposta]:
    """Versões registradas da proposta, da mais recente para a mais antiga."""
    consulta = (
        select(VersaoProposta)
        .where(VersaoProposta.sessao_id == sessao_id)
        .order_by(col(VersaoProposta.numero).desc())
    )
    return list(session.exec(consulta))


def obter_versao_proposta(session: Session, sessao_id: int, numero: int) -> VersaoProposta | None:
    return session.exec(
        select(VersaoProposta).where(
            VersaoProposta.sessao_id == sessao_id, VersaoProposta.numero == numero
        )
    ).first()

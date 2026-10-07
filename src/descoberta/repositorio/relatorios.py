"""Relatórios de Descoberta gerados para uma sessão (por template ou por LLM)."""

from sqlmodel import Session, col, select

from ._comum import exigir_sessao, gravar, opcao, texto_obrigatorio, texto_opcional
from .modelos import OrigemRelatorio, Relatorio


def salvar_relatorio(
    session: Session,
    sessao_id: int,
    *,
    origem: OrigemRelatorio | str,
    conteudo: str,
    modelo: str | None = None,
    versao_prompt: str | None = None,
) -> Relatorio:
    """Guarda uma nova versão do relatório (as anteriores são mantidas).

    Relatório redigido por LLM precisa registrar o modelo e a versão do prompt usados.
    """
    origem = opcao(OrigemRelatorio)("origem", origem)
    conteudo = texto_obrigatorio("conteudo", conteudo)
    modelo = texto_opcional("modelo", modelo)
    versao_prompt = texto_opcional("versao_prompt", versao_prompt)
    if origem == OrigemRelatorio.llm and (modelo is None or versao_prompt is None):
        raise ValueError("relatório por LLM precisa informar modelo e versão do prompt")
    exigir_sessao(session, sessao_id)
    relatorio = Relatorio(
        sessao_id=sessao_id,
        origem=origem,
        conteudo=conteudo,
        modelo=modelo,
        versao_prompt=versao_prompt,
    )
    return gravar(session, relatorio)


def obter_relatorio(session: Session, relatorio_id: int) -> Relatorio | None:
    return session.get(Relatorio, relatorio_id)


def listar_relatorios(session: Session, sessao_id: int) -> list[Relatorio]:
    """Relatórios da sessão, do mais recente para o mais antigo."""
    consulta = (
        select(Relatorio)
        .where(Relatorio.sessao_id == sessao_id)
        .order_by(col(Relatorio.criado_em).desc(), col(Relatorio.id).desc())
    )
    return list(session.exec(consulta))

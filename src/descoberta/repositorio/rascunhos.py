"""Rascunhos do LLM, lista de pessoas citadas e prévia confirmada.

O rascunho fica guardado à parte, com o provedor, o modelo e a versão do prompt. O texto
do consultor só muda quando ele aceita o rascunho, e a cópia do texto e a marcação do
rascunho acontecem numa transação só.
"""

import unicodedata
from collections.abc import Sequence

from sqlmodel import Session, col, select

from ._comum import (
    RegistroNaoEncontrado,
    booleano,
    exigir,
    exigir_sessao,
    gravar,
    id_questionario,
    opcao,
    texto_obrigatorio,
)
from .modelos import (
    DestinoRascunho,
    FaseProposta,
    PessoaCitada,
    PreviaLLM,
    Rascunho,
    SituacaoRascunho,
    TextoSecao,
    agora,
)

# --- Rascunhos ---


def registrar_rascunho(
    session: Session,
    sessao_id: int,
    *,
    destino: DestinoRascunho,
    campo: str,
    texto: str,
    provedor: str,
    modelo: str,
    versao_prompt: str,
    alertas: Sequence[str] = (),
    com_anotacoes_internas: bool = False,
) -> Rascunho:
    """Guarda um rascunho pendente; um pendente anterior do mesmo campo vira substituído."""
    rascunho = Rascunho(
        sessao_id=sessao_id,
        destino=opcao(DestinoRascunho)("destino", destino),
        campo=id_questionario("campo", campo),
        texto=texto_obrigatorio("texto", texto),
        provedor=texto_obrigatorio("provedor", provedor),
        modelo=texto_obrigatorio("modelo", modelo),
        versao_prompt=texto_obrigatorio("versao_prompt", versao_prompt),
        alertas="\n".join(a.strip() for a in alertas if a.strip()) or None,
        com_anotacoes_internas=booleano("com_anotacoes_internas", com_anotacoes_internas),
    )
    exigir_sessao(session, sessao_id)
    anterior = rascunho_pendente(session, sessao_id, rascunho.destino, rascunho.campo)
    if anterior is not None:
        anterior.situacao = SituacaoRascunho.substituido
        anterior.decidido_em = agora()
        session.add(anterior)
    return gravar(session, rascunho)


def rascunhos_da_sessao(
    session: Session,
    sessao_id: int,
    destino: DestinoRascunho | None = None,
    situacao: SituacaoRascunho | None = None,
) -> list[Rascunho]:
    consulta = select(Rascunho).where(Rascunho.sessao_id == sessao_id)
    if destino is not None:
        consulta = consulta.where(Rascunho.destino == destino)
    if situacao is not None:
        consulta = consulta.where(Rascunho.situacao == situacao)
    return list(session.exec(consulta.order_by(col(Rascunho.criado_em), col(Rascunho.id))))


def rascunho_pendente(
    session: Session, sessao_id: int, destino: DestinoRascunho, campo: str
) -> Rascunho | None:
    return session.exec(
        select(Rascunho).where(
            Rascunho.sessao_id == sessao_id,
            Rascunho.destino == destino,
            Rascunho.campo == campo,
            Rascunho.situacao == SituacaoRascunho.pendente,
        )
    ).first()


def _pendente(session: Session, rascunho_id: int) -> Rascunho:
    rascunho = exigir(session, Rascunho, rascunho_id, "rascunho")
    if rascunho.situacao is not SituacaoRascunho.pendente:
        raise ValueError(f"o rascunho {rascunho_id} já foi {rascunho.situacao}")
    return rascunho


def _decidir(rascunho: Rascunho, situacao: SituacaoRascunho) -> None:
    rascunho.situacao = situacao
    rascunho.decidido_em = agora()


def descartar_rascunho(session: Session, rascunho_id: int) -> Rascunho:
    rascunho = _pendente(session, rascunho_id)
    _decidir(rascunho, SituacaoRascunho.descartado)
    return gravar(session, rascunho)


def marcar_rascunho_aceito(session: Session, rascunho_id: int) -> Rascunho:
    """Só marca, sem gravar (a proposta copia o texto e grava junto)."""
    rascunho = _pendente(session, rascunho_id)
    _decidir(rascunho, SituacaoRascunho.aceito)
    session.add(rascunho)
    return rascunho


def aceitar_rascunho_da_revisao(session: Session, rascunho_id: int) -> TextoSecao:
    """Copia o rascunho para o texto da revisão e marca o rascunho como aceito."""
    rascunho = _pendente(session, rascunho_id)
    if rascunho.destino is not DestinoRascunho.revisao:
        raise ValueError(f"o rascunho {rascunho_id} não é de um texto da revisão")
    registro = session.exec(
        select(TextoSecao).where(
            TextoSecao.sessao_id == rascunho.sessao_id, TextoSecao.secao_id == rascunho.campo
        )
    ).first() or TextoSecao(sessao_id=rascunho.sessao_id, secao_id=rascunho.campo, texto="")
    registro.texto = rascunho.texto
    registro.atualizado_em = agora()
    _decidir(rascunho, SituacaoRascunho.aceito)
    session.add(rascunho)
    return gravar(session, registro)


def aceitar_rascunho_da_proposta(session: Session, rascunho_id: int) -> None:
    """Copia o rascunho para o contexto da proposta ou para o objetivo de uma fase
    ("objetivo_fase.<id>") e marca o rascunho como aceito, numa transação só."""
    from .proposta import salvar_texto_proposta  # evita import circular

    rascunho = _pendente(session, rascunho_id)
    if rascunho.destino is not DestinoRascunho.proposta:
        raise ValueError(f"o rascunho {rascunho_id} não é de um texto da proposta")
    if rascunho.campo.startswith("objetivo_fase."):
        fase_id = rascunho.campo.removeprefix("objetivo_fase.")
        if not fase_id.isdigit():
            raise ValueError(f"campo {rascunho.campo!r} inválido")
        fase = session.get(FaseProposta, int(fase_id))
        if fase is None or fase.sessao_id != rascunho.sessao_id:
            raise RegistroNaoEncontrado(f"fase {fase_id} não encontrada nesta proposta")
        fase.objetivo = rascunho.texto
        session.add(fase)
    else:
        salvar_texto_proposta(
            session, rascunho.sessao_id, rascunho.campo, rascunho.texto, gravar_agora=False
        )
    _decidir(rascunho, SituacaoRascunho.aceito)
    session.add(rascunho)
    session.commit()


def descartar_pendentes(session: Session, sessao_id: int, destino: DestinoRascunho) -> None:
    """Descarta os pendentes de um destino (sem commit: quem chama grava junto)."""
    for rascunho in rascunhos_da_sessao(
        session, sessao_id, destino=destino, situacao=SituacaoRascunho.pendente
    ):
        _decidir(rascunho, SituacaoRascunho.descartado)
        session.add(rascunho)


# --- Pessoas citadas ---


def _chave_do_nome(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome)
    return " ".join("".join(c for c in sem_acento if not unicodedata.combining(c)).lower().split())


def pessoas_citadas(session: Session, sessao_id: int) -> list[PessoaCitada]:
    consulta = select(PessoaCitada).where(PessoaCitada.sessao_id == sessao_id)
    return list(session.exec(consulta.order_by(col(PessoaCitada.criado_em), col(PessoaCitada.id))))


def adicionar_pessoa_citada(session: Session, sessao_id: int, nome: str) -> PessoaCitada:
    """Inclui o nome; se ele já está na lista (sem ligar para acento e maiúscula), devolve
    o que já estava."""
    nome = " ".join(texto_obrigatorio("nome", nome).split())
    if len(nome) < 2:
        raise ValueError("o nome precisa de pelo menos 2 letras")
    exigir_sessao(session, sessao_id)
    chave = _chave_do_nome(nome)
    for existente in pessoas_citadas(session, sessao_id):
        if _chave_do_nome(existente.nome) == chave:
            return existente
    return gravar(session, PessoaCitada(sessao_id=sessao_id, nome=nome))


def remover_pessoa_citada(session: Session, pessoa_id: int) -> None:
    session.delete(exigir(session, PessoaCitada, pessoa_id, "pessoa citada"))
    session.commit()


# --- Prévia confirmada ---


def confirmar_previa(session: Session, sessao_id: int, impressao: str) -> PreviaLLM:
    impressao = texto_obrigatorio("impressao", impressao)
    exigir_sessao(session, sessao_id)
    registro = session.get(PreviaLLM, sessao_id) or PreviaLLM(sessao_id=sessao_id, impressao="")
    registro.impressao = impressao
    registro.confirmada_em = agora()
    return gravar(session, registro)


def previa_confirmada(session: Session, sessao_id: int, impressao: str) -> bool:
    registro = session.get(PreviaLLM, sessao_id)
    return registro is not None and registro.impressao == impressao

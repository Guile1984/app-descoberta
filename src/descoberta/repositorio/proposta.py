"""Proposta Comercial: criação (a partir do conteúdo inicial), campos e exclusão.

As fases e os itens da proposta são listas como as da revisão: são editados com
`adicionar_item`, `editar_item` e `excluir_item` (repositorio.revisao).
"""

from typing import Any

from sqlmodel import Session, delete, select

from descoberta.proposta.clausulas import Ajuste
from descoberta.proposta.inicial import PropostaInicial

from ._comum import (
    RegistroNaoEncontrado,
    aplicar_campos,
    booleano,
    cpf_cnpj_opcional,
    email_opcional,
    exigir_sessao,
    gravar,
    id_questionario,
    inteiro,
    texto_obrigatorio,
    texto_opcional,
    uf_opcional,
    validar_campos,
)
from .modelos import (
    ClausulaProposta,
    DestinoRascunho,
    FaseProposta,
    ItemProposta,
    Proposta,
    TipoItemProposta,
    agora,
)
from .rascunhos import descartar_pendentes


def _dias(nome: str, valor: Any) -> int:
    return inteiro(nome, valor, minimo=1)


_VALIDADORES = {
    "cliente_cpf_cnpj": cpf_cnpj_opcional,
    "cliente_representante": texto_opcional,
    "cliente_cargo": texto_opcional,
    "cliente_email": email_opcional,
    "cliente_cidade": texto_opcional,
    "cliente_uf": uf_opcional,
    "condicoes_pagamento": texto_obrigatorio,
    "impostos": texto_obrigatorio,
    "reajuste": texto_obrigatorio,
    "validade_dias": _dias,
}
CAMPOS_PROPOSTA = tuple(_VALIDADORES)


def obter_proposta(session: Session, sessao_id: int) -> Proposta | None:
    return session.get(Proposta, sessao_id)


def criar_proposta(
    session: Session,
    sessao_id: int,
    inicial: PropostaInicial,
    *,
    versao_modelo: int,
    com_alerta: bool = False,
) -> Proposta:
    """Grava a proposta, as fases e os itens numa transação só."""
    exigir_sessao(session, sessao_id)
    if obter_proposta(session, sessao_id) is not None:
        raise ValueError(f"a sessão {sessao_id} já tem proposta")
    proposta = Proposta(
        sessao_id=sessao_id,
        versao_modelo=inteiro("versao_modelo", versao_modelo, minimo=1),
        condicoes_pagamento=inicial.condicoes_pagamento,
        impostos=inicial.impostos,
        reajuste=inicial.reajuste,
        validade_dias=inicial.validade_dias,
        criada_com_alerta=com_alerta,
    )
    session.add(proposta)
    for fase in inicial.fases:
        registro = FaseProposta(
            sessao_id=sessao_id,
            nome=fase.nome,
            objetivo=fase.objetivo,
            duracao_semanas=fase.duracao_semanas,
            investimento=fase.investimento,
        )
        session.add(registro)
        session.flush()  # o id da fase sai daqui, para os itens apontarem para ela
        for tipo, textos in (
            (TipoItemProposta.escopo, fase.escopo),
            (TipoItemProposta.entregavel, fase.entregaveis),
        ):
            for texto in textos:
                session.add(
                    ItemProposta(sessao_id=sessao_id, tipo=tipo, fase_id=registro.id, texto=texto)
                )
    for tipo, textos in (
        (TipoItemProposta.exclusao, inicial.exclusoes),
        (TipoItemProposta.premissa, inicial.premissas),
        (TipoItemProposta.responsabilidade, inicial.responsabilidades),
    ):
        for texto in textos:
            session.add(ItemProposta(sessao_id=sessao_id, tipo=tipo, texto=texto))
    try:
        return gravar(session, proposta)
    except Exception:
        session.rollback()
        raise


def salvar_proposta(session: Session, sessao_id: int, **campos: Any) -> Proposta:
    """Troca só os campos informados (salvamento automático, um campo por vez)."""
    proposta = obter_proposta(session, sessao_id)
    if proposta is None:
        raise RegistroNaoEncontrado(f"a sessão {sessao_id} não tem proposta")
    aplicar_campos(proposta, campos, _VALIDADORES)
    return gravar(session, proposta)


def excluir_proposta(session: Session, sessao_id: int) -> None:
    """Apaga a proposta com as fases, os itens e os ajustes das cláusulas (as versões
    registradas ficam). Os rascunhos pendentes da proposta são descartados: os campos a que
    eles se referem deixam de existir."""
    descartar_pendentes(session, sessao_id, DestinoRascunho.proposta)
    session.exec(delete(ClausulaProposta).where(ClausulaProposta.sessao_id == sessao_id))
    session.exec(delete(ItemProposta).where(ItemProposta.sessao_id == sessao_id))
    session.exec(delete(FaseProposta).where(FaseProposta.sessao_id == sessao_id))
    proposta = obter_proposta(session, sessao_id)
    if proposta is not None:
        session.delete(proposta)
    session.commit()


# --- Ajustes das cláusulas (Condições Gerais) ---


def _ajuste(session: Session, sessao_id: int, clausula_id: str) -> ClausulaProposta | None:
    return session.exec(
        select(ClausulaProposta).where(
            ClausulaProposta.sessao_id == sessao_id,
            ClausulaProposta.clausula_id == clausula_id,
        )
    ).first()


def ajustar_clausula(
    session: Session, sessao_id: int, clausula_id: str, **campos: Any
) -> ClausulaProposta:
    """Troca o texto (`texto`) ou exclui/inclui de volta (`excluida`) uma cláusula.

    Quem chama confere com o modelo se a cláusula existe e se pode ser excluída
    (`proposta.clausulas.conferir_ajuste`).
    """
    clausula_id = id_questionario("clausula_id", clausula_id)
    valores = validar_campos(campos, {"texto": texto_obrigatorio, "excluida": booleano})
    if obter_proposta(session, sessao_id) is None:
        raise RegistroNaoEncontrado(f"a sessão {sessao_id} não tem proposta")
    registro = _ajuste(session, sessao_id, clausula_id) or ClausulaProposta(
        sessao_id=sessao_id, clausula_id=clausula_id
    )
    for nome, valor in valores.items():
        setattr(registro, nome, valor)
    registro.atualizado_em = agora()
    return gravar(session, registro)


def restaurar_clausula(session: Session, sessao_id: int, clausula_id: str) -> None:
    """Volta ao texto do modelo (e inclui a cláusula de volta, se estava excluída)."""
    registro = _ajuste(session, sessao_id, clausula_id)
    if registro is not None:
        session.delete(registro)
        session.commit()


def ajustes_das_clausulas(session: Session, sessao_id: int) -> dict[str, Ajuste]:
    consulta = select(ClausulaProposta).where(ClausulaProposta.sessao_id == sessao_id)
    return {r.clausula_id: Ajuste(r.texto, r.excluida) for r in session.exec(consulta)}

"""Proposta Comercial: criação (a partir do conteúdo inicial), campos e exclusão.

As fases e os itens da proposta são listas como as da revisão: são editados com
`adicionar_item`, `editar_item` e `excluir_item` (repositorio.revisao).
"""

from typing import Any

from sqlmodel import Session, delete

from descoberta.proposta.inicial import PropostaInicial

from ._comum import (
    RegistroNaoEncontrado,
    aplicar_campos,
    cpf_cnpj_opcional,
    email_opcional,
    exigir_sessao,
    gravar,
    inteiro,
    texto_obrigatorio,
    texto_opcional,
)
from .modelos import FaseProposta, ItemProposta, Proposta, TipoItemProposta


def _dias(nome: str, valor: Any) -> int:
    return inteiro(nome, valor, minimo=1)


_VALIDADORES = {
    "cliente_cpf_cnpj": cpf_cnpj_opcional,
    "cliente_representante": texto_opcional,
    "cliente_cargo": texto_opcional,
    "cliente_email": email_opcional,
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
    """Apaga a proposta com as fases e os itens (as versões registradas ficam)."""
    session.exec(delete(ItemProposta).where(ItemProposta.sessao_id == sessao_id))
    session.exec(delete(FaseProposta).where(FaseProposta.sessao_id == sessao_id))
    proposta = obter_proposta(session, sessao_id)
    if proposta is not None:
        session.delete(proposta)
    session.commit()

"""Saídas da revisão pós-sessão: riscos, indicadores, escopo, próximos passos e textos.

As quatro listas funcionam igual (incluir, editar, excluir, listar na ordem de criação),
então usam as mesmas funções, que recebem a tabela: `adicionar_item(session, Risco, …)`.
O que muda de uma tabela para outra está em `_LISTAS`: os validadores de cada campo e
quais campos são obrigatórios.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlmodel import Session, SQLModel, col, select

from descoberta.dominio.revisao import Camada, Nivel, Responsavel

from ._comum import (
    Validadores,
    aplicar_campos,
    booleano,
    dia,
    exigir,
    exigir_sessao,
    gravar,
    id_questionario,
    opcao,
    texto_obrigatorio,
    texto_opcional,
    validar_campos,
)
from .modelos import Indicador, ItemEscopo, ProximoPasso, Risco, TextoSecao, agora


def _data_opcional(nome: str, valor: Any) -> date | None:
    return None if valor is None else dia(nome, valor)


@dataclass(frozen=True)
class _Lista:
    nome: str  # para as mensagens de erro ("risco 3 não encontrado(a)")
    validadores: Validadores
    obrigatorios: tuple[str, ...]


_LISTAS: dict[type[SQLModel], _Lista] = {
    Risco: _Lista(
        "risco",
        {
            "descricao": texto_obrigatorio,
            "categoria": id_questionario,  # a existência no YAML é conferida na web
            "probabilidade": opcao(Nivel),
            "impacto": opcao(Nivel),
            "mitigacao": texto_opcional,
        },
        ("descricao", "categoria", "probabilidade", "impacto"),
    ),
    Indicador: _Lista(
        "indicador",
        {
            "nome": texto_obrigatorio,
            "camada": opcao(Camada),
            "valor_atual": texto_opcional,
            "meta": texto_opcional,
            "prazo": texto_opcional,
            "como_medir": texto_opcional,
        },
        ("nome", "camada"),
    ),
    ItemEscopo: _Lista(
        "item do escopo",
        {"texto": texto_obrigatorio, "entra": booleano},
        ("texto", "entra"),
    ),
    ProximoPasso: _Lista(
        "próximo passo",
        {"acao": texto_obrigatorio, "responsavel": opcao(Responsavel), "prazo": _data_opcional},
        ("acao", "responsavel"),
    ),
}


def adicionar_item[M: SQLModel](session: Session, modelo: type[M], sessao_id: int, **campos) -> M:
    lista = _LISTAS[modelo]
    faltando = [nome for nome in lista.obrigatorios if nome not in campos]
    if faltando:
        raise ValueError(f"{faltando[0]} é obrigatório")
    valores = validar_campos(campos, lista.validadores)
    exigir_sessao(session, sessao_id)
    return gravar(session, modelo(sessao_id=sessao_id, **valores))


def editar_item[M: SQLModel](session: Session, modelo: type[M], item_id: int, **campos) -> M:
    """Troca só os campos informados; se um deles for inválido, nada é gravado."""
    lista = _LISTAS[modelo]
    registro = exigir(session, modelo, item_id, lista.nome)
    aplicar_campos(registro, campos, lista.validadores)
    return gravar(session, registro)


def excluir_item(session: Session, modelo: type[SQLModel], item_id: int) -> None:
    session.delete(exigir(session, modelo, item_id, _LISTAS[modelo].nome))
    session.commit()


def itens_da_sessao[M: SQLModel](session: Session, modelo: type[M], sessao_id: int) -> list[M]:
    """Itens da sessão na ordem em que foram incluídos (é a numeração R1, R2… dos riscos)."""
    consulta = (
        select(modelo)
        .where(modelo.sessao_id == sessao_id)
        .order_by(col(modelo.criado_em), col(modelo.id))
    )
    return list(session.exec(consulta))


# --- Textos das seções do relatório ---


def salvar_texto_secao(
    session: Session, sessao_id: int, secao_id: str, texto: str
) -> TextoSecao | None:
    """Cria ou atualiza o texto da seção; texto em branco apaga (como nas respostas)."""
    secao_id = id_questionario("secao_id", secao_id)
    if not isinstance(texto, str):
        raise TypeError(f"texto precisa ser texto (recebido {texto!r})")
    exigir_sessao(session, sessao_id)
    registro = session.exec(
        select(TextoSecao).where(TextoSecao.sessao_id == sessao_id, TextoSecao.secao_id == secao_id)
    ).first()
    if not texto.strip():
        if registro is not None:
            session.delete(registro)
            session.commit()
        return None
    if registro is None:
        registro = TextoSecao(sessao_id=sessao_id, secao_id=secao_id, texto=texto)
    else:
        registro.texto = texto
        registro.atualizado_em = agora()
    return gravar(session, registro)


def textos_da_sessao(session: Session, sessao_id: int) -> dict[str, str]:
    """Textos da sessão: id da seção → texto."""
    registros = session.exec(select(TextoSecao).where(TextoSecao.sessao_id == sessao_id))
    return {registro.secao_id: registro.texto for registro in registros}

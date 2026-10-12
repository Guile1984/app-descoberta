"""Listas da revisão pós-sessão e da proposta, e os textos do relatório.

As listas (riscos, indicadores, escopo, próximos passos; fases e itens da proposta)
funcionam igual: incluir, editar, excluir, listar na ordem de criação. Por isso usam as
mesmas funções, que recebem a tabela: `adicionar_item(session, Risco, …)`. O que muda de
uma tabela para outra está em `_LISTAS`: os validadores de cada campo, quais campos são
obrigatórios e, quando preciso, uma conferência que depende do banco.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlmodel import Session, SQLModel, col, select

from descoberta.dominio.revisao import Camada, Nivel, Responsavel

from ._comum import (
    Validadores,
    aplicar_campos,
    booleano,
    decimal_opcional,
    dia,
    exigir,
    exigir_sessao,
    gravar,
    id_questionario,
    inteiro,
    opcao,
    texto_obrigatorio,
    texto_opcional,
    validar_campos,
)
from .modelos import (
    DestinoRascunho,
    FaseProposta,
    Indicador,
    ItemEscopo,
    ItemProposta,
    ProximoPasso,
    Risco,
    TextoSecao,
    TipoItemProposta,
    agora,
)


def _data_opcional(nome: str, valor: Any) -> date | None:
    return None if valor is None else dia(nome, valor)


def _semanas(nome: str, valor: Any) -> int | None:
    return None if valor is None else inteiro(nome, valor, minimo=1)


def _id_opcional(nome: str, valor: Any) -> int | None:
    return None if valor is None else inteiro(nome, valor, minimo=1)


def _fase_da_mesma_sessao(session: Session, sessao_id: int, valores: dict[str, Any]) -> None:
    fase_id = valores.get("fase_id")
    if fase_id is None:
        return
    fase = session.get(FaseProposta, fase_id)
    if fase is None or fase.sessao_id != sessao_id:
        raise ValueError(f"a fase {fase_id} não é desta proposta")


Conferencia = Callable[[Session, int, dict[str, Any]], None]


@dataclass(frozen=True)
class _Lista:
    nome: str  # para as mensagens de erro ("risco 3 não encontrado(a)")
    validadores: Validadores
    obrigatorios: tuple[str, ...]
    conferir: Conferencia | None = None  # regra que depende do banco (sessão, valores)


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
    FaseProposta: _Lista(
        "fase",
        {
            "nome": texto_obrigatorio,
            "objetivo": texto_opcional,
            "duracao_semanas": _semanas,
            "investimento": decimal_opcional,
        },
        ("nome",),
    ),
    ItemProposta: _Lista(
        "item da proposta",
        {
            "tipo": opcao(TipoItemProposta),
            "texto": texto_obrigatorio,
            "fase_id": _id_opcional,
        },
        ("tipo", "texto"),
        _fase_da_mesma_sessao,
    ),
}


def adicionar_item[M: SQLModel](session: Session, modelo: type[M], sessao_id: int, **campos) -> M:
    lista = _LISTAS[modelo]
    faltando = [nome for nome in lista.obrigatorios if nome not in campos]
    if faltando:
        raise ValueError(f"{faltando[0]} é obrigatório")
    valores = validar_campos(campos, lista.validadores)
    exigir_sessao(session, sessao_id)
    if lista.conferir:
        lista.conferir(session, sessao_id, valores)
    return gravar(session, modelo(sessao_id=sessao_id, **valores))


def editar_item[M: SQLModel](session: Session, modelo: type[M], item_id: int, **campos) -> M:
    """Troca só os campos informados; se um deles for inválido, nada é gravado."""
    lista = _LISTAS[modelo]
    registro = exigir(session, modelo, item_id, lista.nome)
    if lista.conferir:
        lista.conferir(session, registro.sessao_id, validar_campos(campos, lista.validadores))
    aplicar_campos(registro, campos, lista.validadores)
    return gravar(session, registro)


def excluir_item(session: Session, modelo: type[SQLModel], item_id: int) -> None:
    registro = exigir(session, modelo, item_id, _LISTAS[modelo].nome)
    if isinstance(registro, FaseProposta):
        # O rascunho do objetivo aponta para a fase só pelo texto do campo, e o SQLite pode
        # reaproveitar o id: sem isto, uma fase nova herdaria o rascunho desta.
        from .rascunhos import descartar_pendente_do_campo

        descartar_pendente_do_campo(
            session, registro.sessao_id, DestinoRascunho.proposta, f"objetivo_fase.{item_id}"
        )
    session.delete(registro)
    session.commit()


def itens_da_sessao[M: SQLModel](
    session: Session, modelo: type[M], sessao_id: int, **filtros: Any
) -> list[M]:
    """Itens da sessão na ordem em que foram incluídos (é a numeração R1, R2… dos riscos).

    `filtros`: campo=valor que os itens precisam ter (ex.: tipo="exclusao").
    """
    consulta = select(modelo).where(modelo.sessao_id == sessao_id)
    for campo, valor in filtros.items():
        consulta = consulta.where(getattr(modelo, campo) == valor)
    consulta = consulta.order_by(col(modelo.criado_em), col(modelo.id))
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

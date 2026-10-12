"""Listas editáveis na tela (revisão e proposta): as mesmas rotas e os mesmos templates.

Cada página registra as suas listas com `registrar_rotas_de_listas`, com o nome da página
e o da lista na URL:

    POST /sessoes/1/revisao/riscos              inclui um risco
    GET  /sessoes/1/revisao/riscos/7/editar     o risco 7 em modo de edição
    POST /sessoes/1/revisao/riscos/7            salva a edição
    POST /sessoes/1/revisao/riscos/7/excluir    exclui

Incluir, salvar e excluir devolvem a lista inteira: a numeração (R1, R2…) muda quando um
item sai. Toda mudança dispara o evento da página (ex.: "revisao-mudou"), que faz as
partes que dependem das listas se recarregarem sozinhas.

O que muda de uma lista para outra está em `Lista`: a tabela do banco, os campos do
formulário, como o texto do formulário vira o valor que o repositório espera e, quando
várias listas dividem uma tabela, o filtro (ex.: tipo="exclusao").
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, SQLModel

from descoberta.formatos import numero_campo
from descoberta.questionario import Questionario
from descoberta.repositorio import (
    Sessao,
    adicionar_item,
    editar_item,
    excluir_item,
    itens_da_sessao,
)

from .dependencias import Banco, CatalogoDep, exigir_sessao, html

Formulario = Mapping[str, str]
Conversor = Callable[[Questionario, Formulario], dict[str, Any]]
# Contexto que os templates das listas de uma página precisam (rótulos, fases…).
ContextoDasListas = Callable[[Session, Sessao, Questionario], dict[str, Any]]


@dataclass(frozen=True)
class Lista:
    nome: str  # na URL e nos ids do HTML ("lista-riscos", "riscos-3")
    titulo: str
    explicacao: str
    item: str  # "risco": no botão "Incluir risco"
    modelo: type[SQLModel]
    campos: tuple[str, ...]  # campos do formulário (os mesmos nomes da tabela)
    converter: Conversor
    pagina: str = "revisao"  # na URL e na pasta dos templates
    molde: str | None = None  # _campos_<molde>.html e _leitura_<molde>.html (padrão: o nome)
    filtro: tuple[tuple[str, Any], ...] = ()  # (campo, valor) dos itens desta lista
    # Eventos disparados além do evento da página quando a lista muda (ex.: "fases-mudaram").
    eventos: tuple[str, ...] = ()
    # Evento que faz esta lista se recarregar sozinha (ex.: o escopo, quando as fases mudam,
    # para o seletor de fase mostrar as fases novas).
    recarregar_em: str | None = None

    @property
    def templates(self) -> str:
        return f"{self.pagina}/_%s_{self.molde or self.nome}.html"

    def url(self, sessao_id: int) -> str:
        return f"/sessoes/{sessao_id}/{self.pagina}/{self.nome}"

    def itens(self, banco: Session, sessao_id: int) -> list[SQLModel]:
        return itens_da_sessao(banco, self.modelo, sessao_id, **dict(self.filtro))

    def valores(self, registro: SQLModel) -> dict[str, str]:
        """O registro como o formulário de edição mostra (tudo texto)."""
        valores = {}
        for campo in self.campos:
            valor = getattr(registro, campo)
            if valor is None:
                valor = ""
            elif isinstance(valor, bool):
                valor = "sim" if valor else "nao"
            elif isinstance(valor, date):
                valor = valor.isoformat()  # o <input type="date"> usa AAAA-MM-DD
            elif isinstance(valor, Decimal):
                valor = numero_campo(valor)  # 20000 → "20.000", como o consultor digita
            valores[campo] = str(valor)
        return valores


async def _formulario(request: Request) -> dict[str, str]:
    """Os campos do formulário, quaisquer que sejam (cada lista tem os seus)."""
    formulario = await request.form()
    return {campo: valor for campo, valor in formulario.items() if isinstance(valor, str)}


FormularioDep = Annotated[dict[str, str], Depends(_formulario)]


def registrar_rotas_de_listas(
    router: APIRouter,
    pagina: str,
    listas: Mapping[str, Lista],
    evento: str,
    contexto: ContextoDasListas,
) -> None:
    """Acrescenta ao router as rotas de incluir, mostrar, editar, salvar e excluir.

    Registre-as depois das outras rotas da página: "/sessoes/1/proposta/recriar" também
    combinaria com "/sessoes/1/proposta/{nome}", e vale a rota registrada primeiro.
    """

    def _lista(nome: str) -> Lista:
        if nome not in listas:
            raise HTTPException(404, f"A página não tem a lista '{nome}'.")
        return listas[nome]

    def _exigir_item(banco: Banco, lista: Lista, sessao_id: int, item_id: int) -> SQLModel:
        item = banco.get(lista.modelo, item_id)
        if (
            item is None
            or item.sessao_id != sessao_id
            or any(getattr(item, campo) != valor for campo, valor in lista.filtro)
        ):
            raise HTTPException(404, f"Item {item_id} não encontrado nesta lista.")
        return item

    def _avisar(resposta: HTMLResponse, lista: Lista) -> HTMLResponse:
        # Vários eventos: nomes separados por vírgula (o HTMX dispara cada um).
        resposta.headers["HX-Trigger"] = ", ".join((evento, *lista.eventos))
        return resposta

    def _secao(
        request: Request,
        banco: Banco,
        sessao: Sessao,
        questionario: Questionario,
        lista: Lista,
        valores: Mapping[str, str] | None = None,
        erro: str | None = None,
        focar: bool = False,
    ) -> HTMLResponse:
        """A lista inteira, com o formulário de inclusão (vazio, ou com o que foi digitado e
        o erro). `focar`: depois de incluir, o cursor volta ao primeiro campo (autofocus)."""
        return html(
            request,
            "listas/_lista.html",
            status_code=422 if erro else 200,
            sessao=sessao,
            lista=lista,
            itens=lista.itens(banco, sessao.id),
            valores=valores or {},
            erro=erro,
            focar=focar,
            **contexto(banco, sessao, questionario),
        )

    def _item(request, banco, sessao, questionario, lista, item, **extra) -> HTMLResponse:
        numero = [i.id for i in lista.itens(banco, sessao.id)].index(item.id) + 1
        return html(
            request,
            "listas/_item.html",
            status_code=422 if extra.get("erro") else 200,
            sessao=sessao,
            lista=lista,
            item=item,
            numero=numero,
            **contexto(banco, sessao, questionario),
            **extra,
        )

    def _converter(questionario: Questionario, lista: Lista, formulario: Formulario):
        return {**lista.converter(questionario, formulario), **dict(lista.filtro)}

    base = f"/sessoes/{{sessao_id}}/{pagina}/{{nome}}"

    @router.post(base)
    def incluir(
        request: Request,
        banco: Banco,
        catalogo: CatalogoDep,
        formulario: FormularioDep,
        sessao_id: int,
        nome: str,
    ):
        sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
        lista = _lista(nome)
        try:
            campos = _converter(questionario, lista, formulario)
            adicionar_item(banco, lista.modelo, sessao_id, **campos)
        except (ValueError, TypeError) as erro:
            return _secao(request, banco, sessao, questionario, lista, formulario, str(erro))
        return _avisar(_secao(request, banco, sessao, questionario, lista, focar=True), lista)

    @router.get(base)
    def lista_inteira(
        request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int, nome: str
    ):
        """A lista de novo (quando ela se recarrega sozinha: `Lista.recarregar_em`)."""
        sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
        return _secao(request, banco, sessao, questionario, _lista(nome))

    # {item_id:int}: só números; "/proposta/campo/validade_dias" não cai aqui.
    @router.get(base + "/{item_id:int}")
    def mostrar(
        request: Request,
        banco: Banco,
        catalogo: CatalogoDep,
        sessao_id: int,
        nome: str,
        item_id: int,
    ):
        sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
        lista = _lista(nome)
        item = _exigir_item(banco, lista, sessao_id, item_id)
        return _item(request, banco, sessao, questionario, lista, item)

    @router.get(base + "/{item_id:int}/editar")
    def editar(
        request: Request,
        banco: Banco,
        catalogo: CatalogoDep,
        sessao_id: int,
        nome: str,
        item_id: int,
    ):
        sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
        lista = _lista(nome)
        item = _exigir_item(banco, lista, sessao_id, item_id)
        valores = lista.valores(item)
        return _item(
            request, banco, sessao, questionario, lista, item, editando=True, valores=valores
        )

    @router.post(base + "/{item_id:int}")
    def salvar(
        request: Request,
        banco: Banco,
        catalogo: CatalogoDep,
        formulario: FormularioDep,
        sessao_id: int,
        nome: str,
        item_id: int,
    ):
        sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
        lista = _lista(nome)
        item = _exigir_item(banco, lista, sessao_id, item_id)
        try:
            campos = _converter(questionario, lista, formulario)
            editar_item(banco, lista.modelo, item_id, **campos)
        except (ValueError, TypeError) as erro:
            banco.rollback()
            resposta = _item(
                request,
                banco,
                sessao,
                questionario,
                lista,
                item,
                editando=True,
                valores=formulario,
                erro=str(erro),
            )
            # O formulário de edição mira a lista inteira (hx-target). Com erro, a resposta
            # é só o item em edição: HX-Retarget e HX-Reswap mudam o destino da troca.
            resposta.headers["HX-Retarget"] = f"#{lista.nome}-{item_id}"
            resposta.headers["HX-Reswap"] = "outerHTML"
            return resposta
        return _avisar(_secao(request, banco, sessao, questionario, lista), lista)

    @router.post(base + "/{item_id:int}/excluir")
    def excluir(
        request: Request,
        banco: Banco,
        catalogo: CatalogoDep,
        sessao_id: int,
        nome: str,
        item_id: int,
    ):
        sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
        lista = _lista(nome)
        _exigir_item(banco, lista, sessao_id, item_id)
        excluir_item(banco, lista.modelo, item_id)
        return _avisar(_secao(request, banco, sessao, questionario, lista), lista)

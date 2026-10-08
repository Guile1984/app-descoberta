"""Sinais de alerta: marcar ou desmarcar com um clique (ou Espaço) e anotar uma observação."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request

from descoberta.questionario import Questionario
from descoberta.repositorio import (
    RegistroNaoEncontrado,
    anotar_sinal,
    desmarcar_sinal,
    marcar_sinal,
    sinais_marcados,
)

from ..dependencias import Banco, CatalogoDep, aviso, exigir_sessao, html

router = APIRouter()


def _exigir_sinal(questionario: Questionario, sinal_id: str):
    for bloco in questionario.blocos:
        for sinal in bloco.sinais:
            if sinal.id == sinal_id:
                return sinal
    raise HTTPException(404, f"Sinal '{sinal_id}' não existe no questionário.")


@router.post("/sessoes/{sessao_id}/sinais/{sinal_id}")
def marcar(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    sinal_id: str,
    marcar: Annotated[str, Form()] = "1",
):
    # O botão manda o estado que quer ("1" marca, "0" desmarca), e não "inverta": se o
    # pedido chegar duas vezes, o resultado é o mesmo.
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    sinal = _exigir_sinal(questionario, sinal_id)
    if marcar == "1":
        marcar_sinal(banco, sessao_id, sinal_id)
    else:
        desmarcar_sinal(banco, sessao_id, sinal_id)
    marcados = {s.sinal_id: s for s in sinais_marcados(banco, sessao_id)}
    resposta = html(request, "sessoes/_sinal.html", sessao=sessao, sinal=sinal, marcados=marcados)
    resposta.headers["HX-Trigger"] = "sinais-mudaram"
    return resposta


@router.post("/sessoes/{sessao_id}/sinais/{sinal_id}/observacao")
def observacao(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    sinal_id: str,
    valor: Annotated[str, Form()] = "",
):
    _, questionario = exigir_sessao(banco, catalogo, sessao_id)
    _exigir_sinal(questionario, sinal_id)
    try:
        anotar_sinal(banco, sessao_id, sinal_id, valor)
    except RegistroNaoEncontrado:
        return aviso(request, "marque o sinal antes de escrever a observação")
    return aviso(request)

"""Salvamento automático das respostas: um pedido por pergunta, disparado pelo HTMX."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request

from descoberta.questionario import pergunta_visivel
from descoberta.repositorio import salvar_resposta

from ..dependencias import Banco, CatalogoDep, aviso, exigir_sessao

router = APIRouter()


@router.post("/sessoes/{sessao_id}/respostas/{pergunta_id}")
def salvar(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    pergunta_id: str,
    texto: Annotated[str, Form()] = "",
):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    # A pergunta precisa existir no questionário da versão da sessão e estar visível para
    # o tipo de solução atual (uma condicional escondida não recebe resposta nova).
    try:
        visivel = pergunta_visivel(questionario, pergunta_id, sessao.tipo_solucao)
    except KeyError:
        raise HTTPException(404, f"Pergunta '{pergunta_id}' não existe no questionário.") from None
    if not visivel:
        return aviso(request, "a pergunta não vale para o tipo de solução escolhido")
    salvar_resposta(banco, sessao_id, pergunta_id, texto)  # texto vazio apaga a resposta
    return aviso(request)

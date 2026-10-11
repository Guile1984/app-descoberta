"""Salvamento automático dos números da sessão: métricas e notas dos scores.

Depois de salvar, o cabeçalho HX-Trigger avisa a página ("calculos-mudaram") e o painel
de cálculos se recarrega sozinho.
"""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request

from descoberta.campos import CAMPO_POR_NOME
from descoberta.formatos import ler_decimal
from descoberta.repositorio import salvar_metricas, salvar_nota

from ..dependencias import Banco, CatalogoDep, aviso, exigir_sessao
from ..formularios import inteiro_ou_nada

router = APIRouter()

EVENTO = "calculos-mudaram"


@router.post("/sessoes/{sessao_id}/metricas/{campo}")
def salvar_metrica(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    campo: str,
    valor: Annotated[str, Form()] = "",
):
    exigir_sessao(banco, catalogo, sessao_id)
    if campo not in CAMPO_POR_NOME:
        raise HTTPException(404, f"Métrica '{campo}' não existe.")
    try:
        if campo == "frequencia_periodo":
            convertido = valor or None  # o repositório confere se é dia, semana ou mês
        else:
            convertido = ler_decimal(CAMPO_POR_NOME[campo].rotulo, valor)
        salvar_metricas(banco, sessao_id, **{campo: convertido})
    except (ValueError, TypeError) as erro:
        return aviso(request, str(erro))
    return aviso(request, evento=EVENTO)


@router.post("/sessoes/{sessao_id}/notas/{criterio_id}")
def salvar_nota_criterio(
    request: Request,
    banco: Banco,
    catalogo: CatalogoDep,
    sessao_id: int,
    criterio_id: str,
    valor: Annotated[str, Form()] = "",
):
    _, questionario = exigir_sessao(banco, catalogo, sessao_id)
    scores = questionario.scores
    criterios = {
        c.id for c in (*scores.prontidao_dados.criterios, *scores.viabilidade_final.criterios)
    }
    if criterio_id not in criterios:
        raise HTTPException(404, f"Critério '{criterio_id}' não existe no questionário.")
    if criterio_id == scores.prontidao_dados.criterio_final:
        bloco = scores.prontidao_dados.bloco
        return aviso(request, f"essa nota sai do score de dados (bloco {bloco}), não é dada à mão")
    try:
        salvar_nota(banco, sessao_id, criterio_id, inteiro_ou_nada("A nota", valor))
    except (ValueError, TypeError) as erro:
        return aviso(request, str(erro))
    return aviso(request, evento=EVENTO)

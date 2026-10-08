"""Cronômetro da sessão: um botão (ou Alt+T) inicia, pausa e retoma.

Sem JavaScript: enquanto roda, o próprio cronômetro pede ao servidor uma versão nova a
cada 30 segundos (hx-trigger="every 30s"). Parado, ele não se atualiza.
"""

from fastapi import APIRouter, Request
from sqlmodel import Session

from descoberta.dominio.cronometro import situacao_do_tempo
from descoberta.questionario import Questionario
from descoberta.repositorio import alternar_cronometro, obter_cronometro, tempo_do_cronometro

from ..dependencias import Banco, CatalogoDep, exigir_sessao, html

router = APIRouter()


def contexto_do_cronometro(banco: Session, sessao_id: int, questionario: Questionario) -> dict:
    decorrido, rodando = tempo_do_cronometro(banco, sessao_id)
    minutos = int(decorrido.total_seconds()) // 60
    return {
        "cronometro": {
            "texto": f"{minutos // 60:02d}:{minutos % 60:02d}",
            "rodando": rodando,
            "iniciado": rodando or obter_cronometro(banco, sessao_id) is not None,
            "situacao": situacao_do_tempo(decorrido, questionario.duracao),
            "duracao": questionario.duracao,
        }
    }


def _cronometro(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    sessao, questionario = exigir_sessao(banco, catalogo, sessao_id)
    return html(
        request,
        "sessoes/_cronometro.html",
        sessao=sessao,
        **contexto_do_cronometro(banco, sessao_id, questionario),
    )


@router.get("/sessoes/{sessao_id}/cronometro")
def mostrar(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    return _cronometro(request, banco, catalogo, sessao_id)


@router.post("/sessoes/{sessao_id}/cronometro")
def alternar(request: Request, banco: Banco, catalogo: CatalogoDep, sessao_id: int):
    exigir_sessao(banco, catalogo, sessao_id)
    alternar_cronometro(banco, sessao_id)
    return _cronometro(request, banco, catalogo, sessao_id)

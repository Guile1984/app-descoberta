"""Aplicação FastAPI.

`criar_app()` monta a app apontando para um banco e uma pasta de questionários (os testes
usam um banco temporário); `app` é a instância que o uvicorn roda:

    uv run uvicorn descoberta.web.app:app --reload

O banco vem da variável de ambiente DESCOBERTA_BANCO (ex.: data/demo.db); sem ela, é o
banco real em data/descoberta.db.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from descoberta.repositorio import CAMINHO_BANCO_PADRAO, criar_engine, criar_tabelas

from .catalogo import Catalogo
from .dependencias import html
from .rotas import (
    anotacoes,
    clientes,
    cronometro,
    numeros,
    relatorio,
    respostas,
    revisao,
    sessoes,
    sinais,
)

PASTA_CONFIG_PADRAO = Path("config")
PASTA_STATIC = Path(__file__).parent / "static"


def criar_app(
    caminho_banco: Path | str | None = None, pasta_config: Path | str = PASTA_CONFIG_PADRAO
) -> FastAPI:
    caminho_banco = caminho_banco or os.environ.get("DESCOBERTA_BANCO") or CAMINHO_BANCO_PADRAO

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        # Roda ao ligar a app (antes do primeiro pedido) e, depois do yield, ao desligar.
        app.state.catalogo = Catalogo(pasta_config)
        app.state.engine = criar_engine(caminho_banco)
        criar_tabelas(app.state.engine)
        yield
        app.state.engine.dispose()

    # Sem as páginas automáticas de documentação da API: a app é só a tela do consultor.
    app = FastAPI(
        title="Descoberta",
        lifespan=ciclo_de_vida,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")
    app.include_router(clientes.router)
    app.include_router(sessoes.router)
    app.include_router(respostas.router)
    app.include_router(sinais.router)
    app.include_router(anotacoes.router)
    app.include_router(numeros.router)
    app.include_router(cronometro.router)
    app.include_router(revisao.router)
    app.include_router(relatorio.router)

    @app.exception_handler(HTTPException)
    async def pagina_de_erro(request: Request, erro: HTTPException):
        return html(request, "erro.html", status_code=erro.status_code, mensagem=erro.detail)

    return app


app = criar_app()

"""Proteções para uma app que só deve atender o próprio computador.

A app roda em 127.0.0.1, mas o navegador do consultor também abre outros sites, e um site
malicioso pode tentar usar o navegador como ponte até a app:

- DNS rebinding: o site faz o próprio nome apontar para 127.0.0.1 e lê as páginas da app
  como se fossem dele. Barrado pelo Host: só "127.0.0.1" e "localhost" são aceitos
  (`TrustedHostMiddleware`, do Starlette).
- CSRF: o site envia um formulário escondido para 127.0.0.1:8000. Ele não consegue ler a
  resposta, mas conseguiria gravar ou apagar dados. Barrado aqui: pedidos que gravam só
  passam se o navegador disser que vieram da própria app.

Os navegadores atuais mandam o cabeçalho Sec-Fetch-Site ("same-origin" quando o pedido
vem da própria app, "none" quando o endereço foi digitado). Os mais antigos mandam só o
Origin, comparado com o endereço da app. Sem nenhum dos dois (ferramentas de linha de
comando), o pedido passa: quem roda um programa no computador já tem acesso ao banco.

Não substitui as medidas do guia de produção: com a app exposta à rede, nada disto basta.
"""

from urllib.parse import urlsplit

from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

HOSTS_LOCAIS = ["127.0.0.1", "localhost"]
METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}
_ORIGENS_DA_PROPRIA_APP = {"same-origin", "none"}


class SoDaPropriaApp:
    """Recusa (403) pedidos que gravam e vêm de outro site."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] not in METODOS_SEGUROS:
            cabecalhos = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope["headers"]}
            if not _veio_da_propria_app(cabecalhos):
                resposta = PlainTextResponse(
                    "Pedido recusado: só a própria app pode gravar dados.", status_code=403
                )
                await resposta(scope, receive, send)
                return
        await self.app(scope, receive, send)


def _veio_da_propria_app(cabecalhos: dict[str, str]) -> bool:
    sec_fetch_site = cabecalhos.get("sec-fetch-site")
    if sec_fetch_site is not None:
        return sec_fetch_site in _ORIGENS_DA_PROPRIA_APP
    origem = cabecalhos.get("origin")
    if origem is None:
        return True
    partes = urlsplit(origem)
    return partes.scheme == "http" and partes.netloc.lower() == cabecalhos.get("host", "").lower()

"""Refaz as capturas de tela da documentação (docs/img/) a partir do banco de demonstração.

Uso (na raiz do projeto, com o navegador dos testes instalado):

    uv run playwright install chromium     # uma vez por máquina
    uv run python scripts/capturar_telas.py

Tudo roda nesta máquina: a app sobe numa porta livre, com bancos temporários (o caso
Roberto do demo e um banco vazio, para a tela do primeiro uso). O banco real nunca é
tocado, e as capturas só mostram dados fictícios. O banco temporário não se chama demo.db,
para as telas saírem sem a faixa "Banco de demonstração", como o consultor as vê.

Rode de novo quando a interface mudar e confira as imagens antes do commit.
"""

import socket
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import uvicorn
from playwright.sync_api import Page, sync_playwright

from descoberta.demo import popular_demo
from descoberta.web.app import criar_app

RAIZ = Path(__file__).resolve().parents[1]
PASTA_IMAGENS = RAIZ / "docs" / "img"
# Tela de notebook comum; escala 1 para as imagens ficarem leves.
TAMANHO_DA_TELA = {"width": 1280, "height": 800}
DATA_DA_SESSAO = date(2026, 10, 7)  # data fixa: as capturas não mudam de um dia para outro


def _porta_livre() -> int:
    with socket.socket() as teste:
        teste.bind(("127.0.0.1", 0))
        return teste.getsockname()[1]


@contextmanager
def _app_rodando(caminho_banco: Path) -> Iterator[str]:
    """Liga a app numa porta livre, numa thread, e desliga no fim."""
    app = criar_app(caminho_banco=caminho_banco, pasta_config=RAIZ / "config")
    porta = _porta_livre()
    servidor = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=porta, log_level="warning")
    )
    thread = threading.Thread(target=servidor.run, daemon=True)
    thread.start()
    limite = time.monotonic() + 15
    while not servidor.started:
        if time.monotonic() > limite:
            raise RuntimeError("a app não subiu em 15 s")
        time.sleep(0.05)
    try:
        yield f"http://127.0.0.1:{porta}"
    finally:
        servidor.should_exit = True
        thread.join(timeout=10)


def _salvar(page: Page, nome: str, seletor: str | None = None) -> None:
    caminho = PASTA_IMAGENS / nome
    if seletor:
        page.locator(seletor).screenshot(path=caminho)
    else:
        page.screenshot(path=caminho)
    print(f"  {caminho.relative_to(RAIZ).as_posix()}")


def _capturas_do_demo(page: Page, sessao: str) -> list[tuple[str, Callable[[], None]]]:
    def abrir(url: str, esperar: str = "main") -> None:
        page.goto(url)
        page.locator(esperar).first.wait_for()

    def sessao_bloco_1() -> None:
        abrir(f"{sessao}?bloco=1", "#calculos")
        _salvar(page, "sessao-bloco-1.png")

    def bloco_4() -> None:
        abrir(f"{sessao}?bloco=4", "fieldset.numeros")
        page.locator("fieldset.numeros").last.scroll_into_view_if_needed()
        _salvar(page, "sessao-score-dados.png", "fieldset.numeros >> nth=-1")

    def calculos() -> None:
        abrir(f"{sessao}?bloco=10", "#calculos")
        _salvar(page, "sessao-calculos.png", "#calculos")

    def atalhos() -> None:
        abrir(f"{sessao}?bloco=1", "#calculos")
        page.keyboard.press("Control+/")
        page.locator("#ajuda-atalhos").wait_for(state="visible")
        _salvar(page, "sessao-atalhos.png", "#ajuda-atalhos")
        page.keyboard.press("Escape")

    def encerramento() -> None:
        abrir(f"{sessao}/encerramento", "#resumo-leitura")
        _salvar(page, "sessao-encerramento.png", "#resumo-leitura")

    def revisao() -> None:
        abrir(f"{sessao}/revisao", "#pendencias-revisao")
        _salvar(page, "revisao.png")
        page.locator("#matriz-riscos").scroll_into_view_if_needed()
        _salvar(page, "revisao-matriz.png", "#matriz-riscos")

    def relatorio() -> None:
        abrir(f"{sessao}/relatorio", "article.documento")
        _salvar(page, "relatorio.png")

    def proposta() -> None:
        abrir(f"{sessao}/proposta/documento", "article.documento")
        _salvar(page, "proposta.png")

    return [
        ("sessão", sessao_bloco_1),
        ("score de dados", bloco_4),
        ("cálculos", calculos),
        ("atalhos", atalhos),
        ("encerramento", encerramento),
        ("revisão", revisao),
        ("relatório", relatorio),
        ("proposta", proposta),
    ]


def main() -> int:
    PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as pasta:
        roberto = Path(pasta) / "capturas.db"
        sessao_id = popular_demo(roberto, hoje=DATA_DA_SESSAO)
        with (
            sync_playwright() as playwright,
            _app_rodando(Path(pasta) / "vazio.db") as base_vazia,
            _app_rodando(roberto) as base,
        ):
            navegador = playwright.chromium.launch()
            page = navegador.new_page(viewport=TAMANHO_DA_TELA, locale="pt-BR")
            print("Capturas em docs/img/:")
            # Primeiro uso: num banco vazio, a tela inicial pede o perfil do consultor.
            page.goto(base_vazia)
            page.locator("form").wait_for()
            _salvar(page, "perfil-primeiro-uso.png")
            for _nome, capturar in _capturas_do_demo(page, f"{base}/sessoes/{sessao_id}"):
                capturar()
            navegador.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

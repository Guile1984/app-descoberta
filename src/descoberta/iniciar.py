"""Liga a app e abre o navegador: `uv run --no-dev python -m descoberta` (o iniciar.bat faz isso).

O servidor escuta só em 127.0.0.1, o próprio computador, e não há opção para mudar isso:
a app é feita para um único usuário, no notebook dele (veja SECURITY.md).

Se a porta já está em uso pela própria app (o consultor deu dois cliques de novo), não é
erro: só abre o navegador nela. Para saber se é a própria app, pergunta em `/_identidade`.
"""

import argparse
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

import uvicorn

HOST = "127.0.0.1"
PORTA_PADRAO = 8000
# O que a rota /_identidade responde: outro programa na mesma porta não responde isto.
IDENTIDADE = "app-descoberta"


def endereco(porta: int) -> str:
    return f"http://{HOST}:{porta}"


def configuracao(porta: int) -> uvicorn.Config:
    return uvicorn.Config("descoberta.web.app:app", host=HOST, port=porta, log_level="warning")


def ler_argumentos(argumentos: list[str]) -> argparse.Namespace:
    leitor = argparse.ArgumentParser(
        prog="python -m descoberta",
        description="Liga a App de Descoberta neste computador e abre o navegador.",
    )
    leitor.add_argument("--porta", type=int, default=PORTA_PADRAO, help="padrão: 8000")
    leitor.add_argument("--sem-navegador", action="store_true", help="não abre o navegador sozinho")
    return leitor.parse_args(argumentos)


def porta_livre(porta: int) -> bool:
    with socket.socket() as teste:
        try:
            teste.bind((HOST, porta))
        except OSError:
            return False
    return True


def app_ja_aberta(porta: int) -> bool:
    """A porta está com a própria app (e não com outro programa)?"""
    try:
        # O endereço é sempre http://127.0.0.1 (montado aqui, nunca vindo de fora).
        with urllib.request.urlopen(f"{endereco(porta)}/_identidade", timeout=3) as resposta:  # noqa: S310
            return resposta.read(100).decode("utf-8", "replace") == IDENTIDADE
    except (OSError, ValueError):
        return False


def aviso_porta_ocupada(porta: int) -> str:
    return (
        f"A porta {porta} já está em uso por outro programa.\n"
        f"Para usar outra porta: uv run --no-dev python -m descoberta --porta {porta + 1}"
    )


def como_encerrar(url: str) -> str:
    return (
        f"App de Descoberta aberta em {url}\n"
        "\n"
        "Para encerrar a app: feche esta janela (ou tecle Ctrl+C nela).\n"
        "Fechar o navegador não encerra a app: deixe esta janela aberta enquanto usa."
    )


def _abrir_navegador_quando_pronto(servidor: uvicorn.Server, url: str) -> None:
    limite = time.monotonic() + 60
    while not servidor.started and time.monotonic() < limite:
        time.sleep(0.1)
    if servidor.started:
        webbrowser.open(url)


def main(argumentos: list[str] | None = None) -> int:
    opcoes = ler_argumentos(sys.argv[1:] if argumentos is None else argumentos)
    url = endereco(opcoes.porta)
    if not porta_livre(opcoes.porta):
        if app_ja_aberta(opcoes.porta):
            print(f"A app já está aberta em {url}. Abrindo o navegador.")
            print("Para encerrar a app, feche a outra janela preta (a que foi aberta antes).")
            if not opcoes.sem_navegador:
                webbrowser.open(url)
            return 0
        print(aviso_porta_ocupada(opcoes.porta))
        return 1
    servidor = uvicorn.Server(configuracao(opcoes.porta))
    if not opcoes.sem_navegador:
        threading.Thread(
            target=_abrir_navegador_quando_pronto, args=(servidor, url), daemon=True
        ).start()
    print(como_encerrar(url), flush=True)
    servidor.run()
    return 0

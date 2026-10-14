"""Liga a app e abre o navegador: `uv run --no-dev python -m descoberta` (o iniciar.bat faz isso).

O servidor escuta só em 127.0.0.1, o próprio computador, e não há opção para mudar isso:
a app é feita para um único usuário, no notebook dele (veja SECURITY.md).
"""

import argparse
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

HOST = "127.0.0.1"
PORTA_PADRAO = 8000


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


def aviso_porta_ocupada(porta: int) -> str:
    return (
        f"A porta {porta} já está em uso: a app talvez já esteja aberta em {endereco(porta)}.\n"
        f"Para usar outra porta: uv run --no-dev python -m descoberta --porta {porta + 1}"
    )


def _abrir_navegador_quando_pronto(servidor: uvicorn.Server, url: str) -> None:
    limite = time.monotonic() + 60
    while not servidor.started and time.monotonic() < limite:
        time.sleep(0.1)
    if servidor.started:
        webbrowser.open(url)


def main(argumentos: list[str] | None = None) -> int:
    opcoes = ler_argumentos(sys.argv[1:] if argumentos is None else argumentos)
    if not porta_livre(opcoes.porta):
        print(aviso_porta_ocupada(opcoes.porta))
        return 1
    url = endereco(opcoes.porta)
    servidor = uvicorn.Server(configuracao(opcoes.porta))
    if not opcoes.sem_navegador:
        threading.Thread(
            target=_abrir_navegador_quando_pronto, args=(servidor, url), daemon=True
        ).start()
    print(f"App de Descoberta em {url}  (para fechar: Ctrl+C ou feche esta janela)")
    servidor.run()
    return 0

"""Liga a app e abre o navegador: `uv run --no-dev python -m descoberta` (o iniciar.bat faz isso).

O servidor escuta só em 127.0.0.1, o próprio computador, e não há opção para mudar isso:
a app é feita para um único usuário, no notebook dele (veja SECURITY.md).

Se a porta já está em uso pela própria app (o consultor deu dois cliques de novo), não é
erro: só abre o navegador nela. Para saber se é a própria app, pergunta em `/_identidade`.

Ctrl+C no Windows: normalmente o console avisa o Python *e* o cmd.exe que roda o
iniciar.bat; o Python mostra um traceback e o cmd pergunta "Deseja finalizar o arquivo em
lotes (S/N)?". Enquanto a app roda, o Ctrl+C vira uma tecla comum no console
(`_ctrl_c_como_tecla`): ninguém recebe o sinal, e a própria app lê a tecla e encerra.
"""

import argparse
import contextlib
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
# Segundos que a janela do segundo clique duplo fica aberta antes de fechar sozinha.
ESPERA_JANELA_REPETIDA = 5
APP_ENCERRADA = "App encerrada. Pode fechar esta janela."
CTRL_C = "\x03"


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


def _ctrl_c_como_tecla():
    """No console do Windows, faz o Ctrl+C virar uma tecla comum, e não um sinal.

    Devolve uma função que desfaz a mudança, ou None fora de um console do Windows (nos
    testes, por exemplo), onde nada muda e o Ctrl+C continua sendo um KeyboardInterrupt.
    """
    if sys.platform != "win32":
        return None
    import ctypes

    kernel32 = ctypes.windll.kernel32
    entrada = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
    modo = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(entrada, ctypes.byref(modo)):
        return None
    ENABLE_PROCESSED_INPUT = 0x0001  # com ele ligado, o Ctrl+C vira sinal
    if not kernel32.SetConsoleMode(entrada, modo.value & ~ENABLE_PROCESSED_INPUT):
        return None
    return lambda: kernel32.SetConsoleMode(entrada, modo.value)


def _vigiar_ctrl_c(servidor: uvicorn.Server, tecla_disponivel, ler_tecla) -> None:
    """Lê as teclas da janela enquanto a app roda; com Ctrl+C, pede para o servidor parar."""
    while not servidor.should_exit:
        if tecla_disponivel():
            if ler_tecla() == CTRL_C:
                servidor.should_exit = True
        else:
            time.sleep(0.1)


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
            print("Para encerrar a app, use a outra janela preta (a que foi aberta antes).")
            print(f"Esta janela fecha sozinha em {ESPERA_JANELA_REPETIDA} segundos.", flush=True)
            if not opcoes.sem_navegador:
                webbrowser.open(url)
            time.sleep(ESPERA_JANELA_REPETIDA)
            return 0
        print(aviso_porta_ocupada(opcoes.porta))
        return 1
    servidor = uvicorn.Server(configuracao(opcoes.porta))
    if not opcoes.sem_navegador:
        threading.Thread(
            target=_abrir_navegador_quando_pronto, args=(servidor, url), daemon=True
        ).start()
    print(como_encerrar(url), flush=True)
    desfazer = _ctrl_c_como_tecla()
    try:
        if desfazer:
            import msvcrt

            threading.Thread(
                target=_vigiar_ctrl_c, args=(servidor, msvcrt.kbhit, msvcrt.getwch), daemon=True
            ).start()
        # Fora do console do Windows (ou se o modo não mudou), o Ctrl+C ainda é sinal.
        with contextlib.suppress(KeyboardInterrupt):
            servidor.run()
        print(f"\n{APP_ENCERRADA}", flush=True)
        if desfazer:
            import msvcrt

            msvcrt.getwch()  # a janela fica com a mensagem até teclar algo ou fechá-la
    finally:
        if desfazer:
            desfazer()
    return 0

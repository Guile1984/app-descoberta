"""Início com dois cliques (iniciar.bat → `python -m descoberta`), sempre só em 127.0.0.1."""

import http.server
import re
import socket
import threading
from pathlib import Path

import pytest

from descoberta import iniciar

RAIZ = Path(__file__).resolve().parents[1]


def test_servidor_so_escuta_o_proprio_computador():
    config = iniciar.configuracao(porta=8123)
    assert config.host == "127.0.0.1"
    assert config.port == 8123


def test_nao_ha_opcao_para_mudar_o_host():
    with pytest.raises(SystemExit):
        iniciar.ler_argumentos(["--host", "0.0.0.0"])


def test_porta_padrao_e_8000():
    assert iniciar.ler_argumentos([]).porta == 8000
    assert iniciar.ler_argumentos(["--porta", "8001"]).porta == 8001


def test_porta_ocupada_vira_mensagem_clara():
    with socket.socket() as ocupado:
        ocupado.bind(("127.0.0.1", 0))
        ocupado.listen()
        porta = ocupado.getsockname()[1]
        assert not iniciar.porta_livre(porta)
        mensagem = iniciar.aviso_porta_ocupada(porta)
    assert str(porta) in mensagem
    assert "--porta" in mensagem


def test_endereco_aberto_no_navegador():
    assert iniciar.endereco(8000) == "http://127.0.0.1:8000"


def test_iniciar_bat_usa_o_inicializador_e_nunca_abre_para_a_rede():
    texto = (RAIZ / "iniciar.bat").read_text(encoding="utf-8")
    assert "python -m descoberta" in texto
    assert "0.0.0.0" not in texto
    assert not re.search(r"--host", texto)
    assert 'cd /d "%~dp0"' in texto  # roda na pasta do projeto (config/ e data/)


def test_iniciar_bat_tem_finais_de_linha_do_windows():
    # O cmd.exe se confunde com arquivos .bat que têm só LF (rótulos e GOTO falham).
    conteudo = (RAIZ / "iniciar.bat").read_bytes()
    assert b"\r\n" in conteudo
    assert b"\n" not in conteudo.replace(b"\r\n", b"")


def test_iniciar_bat_so_usa_sintaxe_do_cmd():
    # Redirecionamentos do Bash (/dev/null) viram erro no cmd.exe: "O sistema não pode
    # encontrar o caminho especificado".
    texto = (RAIZ / "iniciar.bat").read_text(encoding="utf-8")
    assert "/dev/null" not in texto
    assert "where uv >nul 2>nul" in texto


def test_iniciar_bat_instala_so_o_que_a_app_usa():
    texto = (RAIZ / "iniciar.bat").read_text(encoding="utf-8")
    assert texto.count("uv run --no-dev --frozen") == 2


# --- A app já aberta e como encerrar -------------------------------------------------


class _ServidorFalso:
    """Servidor HTTP mínimo numa porta livre, respondendo `texto` em qualquer endereço."""

    def __init__(self, texto: str):
        texto_bytes = texto.encode()

        class Responder(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(texto_bytes)

            def log_message(self, *args):
                pass

        self.servidor = http.server.HTTPServer(("127.0.0.1", 0), Responder)
        self.porta = self.servidor.server_address[1]

    def __enter__(self):
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *args):
        self.servidor.shutdown()
        self.servidor.server_close()


def test_reconhece_a_propria_app_na_porta():
    with _ServidorFalso(iniciar.IDENTIDADE) as falso:
        assert iniciar.app_ja_aberta(falso.porta)


def test_outro_programa_na_porta_nao_e_a_app():
    with _ServidorFalso("<html>outro programa</html>") as falso:
        assert not iniciar.app_ja_aberta(falso.porta)


def test_porta_sem_ninguem_nao_e_a_app():
    with socket.socket() as livre:
        livre.bind(("127.0.0.1", 0))
        porta = livre.getsockname()[1]
    assert not iniciar.app_ja_aberta(porta)


def test_app_ja_aberta_so_abre_o_navegador(monkeypatch, capsys):
    abertos = []
    monkeypatch.setattr(iniciar, "porta_livre", lambda porta: False)
    monkeypatch.setattr(iniciar, "app_ja_aberta", lambda porta: True)
    monkeypatch.setattr(iniciar.webbrowser, "open", abertos.append)
    monkeypatch.setattr(iniciar.uvicorn.Server, "run", lambda self: pytest.fail("subiu outra"))

    assert iniciar.main([]) == 0
    assert abertos == ["http://127.0.0.1:8000"]
    assert "a app já está aberta" in capsys.readouterr().out.lower()


def test_app_ja_aberta_sem_navegador_nao_abre_nada(monkeypatch):
    monkeypatch.setattr(iniciar, "porta_livre", lambda porta: False)
    monkeypatch.setattr(iniciar, "app_ja_aberta", lambda porta: True)
    monkeypatch.setattr(iniciar.webbrowser, "open", lambda url: pytest.fail("abriu"))
    assert iniciar.main(["--sem-navegador"]) == 0


def test_porta_ocupada_por_outro_programa_continua_erro(monkeypatch, capsys):
    monkeypatch.setattr(iniciar, "porta_livre", lambda porta: False)
    monkeypatch.setattr(iniciar, "app_ja_aberta", lambda porta: False)
    assert iniciar.main(["--sem-navegador"]) == 1
    assert "--porta 8001" in capsys.readouterr().out


def test_janela_explica_como_encerrar(monkeypatch, capsys):
    monkeypatch.setattr(iniciar, "porta_livre", lambda porta: True)
    monkeypatch.setattr(iniciar.uvicorn.Server, "run", lambda self: None)
    assert iniciar.main(["--sem-navegador"]) == 0
    saida = capsys.readouterr().out.lower()
    assert "para encerrar a app" in saida
    assert "ctrl+c" in saida
    assert "fechar o navegador não encerra" in saida


# --- .env -----------------------------------------------------------------------------


def test_iniciar_bat_carrega_o_env_so_se_existir():
    texto = (RAIZ / "iniciar.bat").read_text(encoding="utf-8")
    assert "if exist .env" in texto
    assert "--env-file .env" in texto


def test_iniciar_bat_avisa_env_salvo_como_txt():
    # O Bloco de Notas salva ".env" como ".env.txt" quando a extensão está oculta.
    texto = (RAIZ / "iniciar.bat").read_text(encoding="utf-8")
    assert "if exist .env.txt" in texto


# --- Encerramento sem traceback e sem a pergunta do arquivo em lotes ------------------


def test_ctrl_c_encerra_sem_traceback(monkeypatch, capsys):
    def interromper(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(iniciar, "porta_livre", lambda porta: True)
    monkeypatch.setattr(iniciar.uvicorn.Server, "run", interromper)
    assert iniciar.main(["--sem-navegador"]) == 0
    assert "App encerrada. Pode fechar esta janela." in capsys.readouterr().out


def test_ctrl_c_como_tecla_pede_para_o_servidor_parar():
    servidor = iniciar.uvicorn.Server(iniciar.configuracao(8000))
    teclas = iter(["a", "\x03"])
    iniciar._vigiar_ctrl_c(servidor, tecla_disponivel=lambda: True, ler_tecla=lambda: next(teclas))
    assert servidor.should_exit


def test_vigia_para_quando_o_servidor_ja_parou():
    servidor = iniciar.uvicorn.Server(iniciar.configuracao(8000))
    servidor.should_exit = True
    iniciar._vigiar_ctrl_c(
        servidor, tecla_disponivel=lambda: True, ler_tecla=lambda: pytest.fail("leu tecla")
    )


def test_fora_do_console_do_windows_nao_mexe_no_ctrl_c():
    # Nos testes a entrada não é um console: o Ctrl+C continua como sinal (KeyboardInterrupt).
    assert iniciar._ctrl_c_como_tecla() is None


def test_segunda_janela_fecha_sozinha(monkeypatch, capsys):
    esperas = []
    monkeypatch.setattr(iniciar, "porta_livre", lambda porta: False)
    monkeypatch.setattr(iniciar, "app_ja_aberta", lambda porta: True)
    monkeypatch.setattr(iniciar.webbrowser, "open", lambda url: None)
    monkeypatch.setattr(iniciar.time, "sleep", esperas.append)
    assert iniciar.main([]) == 0
    assert esperas == [iniciar.ESPERA_JANELA_REPETIDA]
    assert "fecha sozinha" in capsys.readouterr().out


def test_iniciar_bat_so_pausa_quando_ha_erro():
    # Sucesso (app encerrada ou já aberta) fecha a janela; erro (porta de outro programa,
    # falha do uv) deixa a mensagem na tela até teclar algo.
    linhas = (RAIZ / "iniciar.bat").read_text(encoding="utf-8").splitlines()
    assert linhas[-1] == "if errorlevel 1 pause"
    assert "pause" not in linhas  # o único "pause" solto é o do uv ausente, indentado

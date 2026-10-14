"""Início com dois cliques (iniciar.bat → `python -m descoberta`), sempre só em 127.0.0.1."""

import re
import socket
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

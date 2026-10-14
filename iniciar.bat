@echo off
rem Liga a App de Descoberta e abre o navegador. Basta dar dois cliques neste arquivo.
rem A app escuta so neste computador (127.0.0.1); nunca fica aberta para a rede.
chcp 65001 >nul
cd /d "%~dp0"

where uv >/dev/null 2>nul
if errorlevel 1 (
    echo O uv nao esta instalado. Veja o passo 1 da instalacao no README.md.
    pause
    exit /b 1
)

rem Na primeira vez, o uv baixa o Python e as bibliotecas (alguns minutos, com internet).
if exist .env (
    uv run --env-file .env python -m descoberta %*
) else (
    uv run python -m descoberta %*
)
pause

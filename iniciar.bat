@echo off
rem Liga a App de Descoberta e abre o navegador. Basta dar dois cliques neste arquivo.
rem A app escuta so neste computador (127.0.0.1); nunca fica aberta para a rede.
chcp 65001 >nul
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo O uv nao esta instalado. Veja o passo 1 da instalacao no README.md.
    pause
    exit /b 1
)

rem Na primeira vez, o uv baixa o Python e as bibliotecas (alguns minutos, com internet).
rem --no-dev: so o que a app usa (sem as ferramentas de teste); --frozen: as versoes exatas do uv.lock.
rem O .env (configuracao do LLM) e lido se existir. Com a extensao oculta, o Bloco de Notas
rem costuma salvar ".env.txt", que o uv nao le: avisamos.
if exist .env.txt if not exist .env (
    echo Aviso: encontrei ".env.txt", mas o nome precisa ser ".env", sem o ".txt".
    echo Sem ele, os rascunhos por LLM ficam desligados. Veja o README.
    echo.
)
if exist .env (
    echo Configuracoes lidas do arquivo .env.
    uv run --no-dev --frozen --env-file .env python -m descoberta %*
) else (
    uv run --no-dev --frozen python -m descoberta %*
)
pause

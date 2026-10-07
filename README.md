# App de Descoberta para IA

App local para conduzir ao vivo sessões de descoberta com clientes PME que desejam
soluções de IA e gerar o Relatório de Descoberta. Veja `docs/especificacao.md`.

> Em desenvolvimento. Projeto desenvolvido com Claude Code sob direção e revisão do autor.

## Comandos

```bash
uv sync                                   # instalar
uv run pytest --cov=descoberta            # testes
uv run ruff check . && uv run ruff format --check .   # lint
uv run pre-commit install                 # ativar hooks no git
```

## Rodar a app

Rode os comandos na raiz do projeto (a app lê `config/` e grava em `data/`).

```bash
uv run uvicorn descoberta.web.app:app --reload   # abre em http://127.0.0.1:8000
```

O banco real fica em `data/descoberta.db` (fora do Git). Para usar outro arquivo, defina a
variável `DESCOBERTA_BANCO`.

### Demonstração com o caso Roberto

```powershell
uv run python -m descoberta.demo                 # (re)cria data/demo.db
$env:DESCOBERTA_BANCO = "data/demo.db"           # PowerShell
uv run uvicorn descoberta.web.app:app --reload
```

No Bash: `DESCOBERTA_BANCO=data/demo.db uv run uvicorn descoberta.web.app:app --reload`.
O comando de demonstração recria só o `data/demo.db` e nunca toca no banco real.

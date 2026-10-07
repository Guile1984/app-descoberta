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

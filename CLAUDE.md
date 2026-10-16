# CLAUDE.md — App de Descoberta para IA

## Contexto do projeto
App local (notebook) para conduzir ao vivo sessões de descoberta com clientes PME
que desejam soluções de IA, seguindo o "Modelo de Descoberta — Apps de IA para PMEs"
(10 blocos + encerramento). Gera o Relatório de Descoberta por template e por LLM.

Usuário único (consultor). A app DEVE funcionar sem internet durante a sessão.
O LLM só é usado depois da sessão, para o rascunho do relatório.

## Modo de trabalho
- Você (Claude Code) implementa de ponta a ponta. O dono do produto (Gui) aprova
  planos, revisa diffs e valida a app rodando.
- Trabalhe um sprint por vez, na ordem da especificação. Não avance de sprint sem
  aprovação explícita.
- No início de cada sprint: apresente o plano (arquivos, decisões, testes) e espere
  aprovação.
- TDD: escreva os testes antes da implementação.
- Ao fim de cada sprint: `uv run pytest` e `uv run ruff check .` passando, resumo
  do que mudou, como testar manualmente e entrada no CHANGELOG.md.
- Explique decisões não óbvias em linguagem simples (Gui está aprendendo HTMX).
- Responda em português do Brasil. Código, nomes de variáveis e commits podem ser
  em português, de forma consistente.

## Stack
- Python 3.12+, gerenciado com uv
- FastAPI + Jinja2 + HTMX (JS mínimo: atalhos de teclado e avisos de falha de salvamento)
- SQLite + SQLModel
- Pydantic para validar o questionário (YAML)
- Exportação: Markdown, DOCX, PDF
- Qualidade: pytest (+ cobertura), Playwright (testes e2e no navegador), ruff, pre-commit

## Arquitetura (dependências apontam para dentro)
```
src/descoberta/
  questionario/   # carrega e valida o YAML; resolve condicionais
  dominio/        # cálculos e regras puras (sem banco, sem web)
  repositorio/    # SQLModel + SQLite
  relatorio/      # template do relatório e exportadores
  llm/            # provedor abstrato, anonimização, prompts versionados
  web/            # rotas FastAPI, templates Jinja2, HTMX
config/
  questionario_v1.yaml
prompts/
  relatorio_v1.md
tests/
```
- `dominio` nunca importa `web`, `repositorio` ou `llm`.
- O questionário NUNCA é escrito no código: vem do YAML. Cada sessão registra a
  versão do questionário usada.
- Métricas numéricas ficam em campos próprios; nunca extrair números do texto.

## Regras de negócio essenciais
- Score de prontidão de dados: 5 critérios × 0–3 (máx. 15).
  < 6 → fase 0; 6–10 → MVP com ressalvas; > 10 → pronto.
- Payback (meses) = investimento / (economia mensal − custo mensal de operação).
- Score final de viabilidade: 6 critérios × 0–3 (máx. 18).
  14–18 → seguir; 9–13 → seguir com fase 0; < 9 → não seguir agora.
- Caso de teste de referência ("Construtora Alvorada / Roberto"):
  60 h/mês de dor; score de dados 4; investimento R$ 20.000; economia R$ 3.000/mês;
  operação R$ 400/mês; payback ≈ 7,7 meses; score final 12 → seguir com fase 0.

## Segurança e LGPD
- Dados ficam locais; banco SQLite fora do Git.
- Antes de qualquer chamada ao LLM, anonimizar nomes, CPFs, telefones, e-mails e
  endereços com marcadores; desfazer localmente na resposta.
- Teste automatizado garantindo que o payload enviado não contém dados pessoais.
- Chave de API só em variável de ambiente (.env no .gitignore).
- Sem internet ou com erro na API: oferecer o relatório por template.
- Guardar modelo e versão do prompt em cada relatório gerado.

## Comandos
- Instalar: `uv sync`
- Rodar: `uv run uvicorn descoberta.web.app:app --reload`
- Testes: `uv run pytest --cov=descoberta` (todos, inclusive os e2e no navegador)
- Testes rápidos, sem navegador: `uv run pytest -m "not e2e"`
- Navegador dos testes e2e (uma vez por máquina): `uv run playwright install chromium`
- Lint: `uv run ruff check . && uv run ruff format --check .`
- Documentação: `uv run --group docs mkdocs build --strict` (site em `docs/`, conferido
  com o código por `tests/test_documentacao.py`); capturas: `uv run python scripts/capturar_telas.py`
- Migração nova (depois de mudar um modelo): `uv run alembic upgrade head` e
  `uv run alembic revision --autogenerate --rev-id NNNN -m "..."`; revisar o arquivo gerado.

## Não fazer
- Não adicionar dependências sem justificar no plano do sprint.
- Não usar LLM para cálculos, condicionais ou qualquer lógica determinística.
- Não introduzir React ou build de frontend.
- Não pular testes para "terminar mais rápido".

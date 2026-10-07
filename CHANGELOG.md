# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [0.1.0] — 2026-10-07 — Sprint 0: Setup

### Adicionado
- Projeto Python gerenciado com uv (layout `src/`, Python ≥ 3.12).
- Pacote `descoberta` com as camadas `questionario`, `dominio`, `repositorio`,
  `relatorio`, `llm` e `web` (vazias), além das pastas `config/` e `prompts/`.
- Ferramentas de desenvolvimento: pytest + pytest-cov, ruff (lint e formatação), pre-commit.
- Teste automático da regra de arquitetura: `dominio` não importa `web`,
  `repositorio` nem `llm`.
- CI no GitHub Actions rodando ruff e pytest a cada push e pull request.
- `.gitignore` (banco SQLite, `.env` e exportações fora do Git), `.env.example`,
  `.gitattributes` (fim de linha LF).

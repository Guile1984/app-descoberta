# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [0.3.0] — 2026-10-07 — Sprint 2: Cálculos

### Adicionado
- `descoberta.dominio`: cálculos puros, com dinheiro e horas em `Decimal` (float é recusado).
  - `dor`: `ocorrencias_por_mes()` (dia → × 22 dias úteis; semana → × 52/12),
    `horas_dor_mes()` e `custo_dor_mes()`.
  - `operacao`: `custo_operacao_mes()` = chamadas/dia × custo por chamada × 22 + custo fixo.
  - `payback`: `economia_mes()` = horas economizadas × custo da hora + outros ganhos
    (opcional, padrão 0); `payback_meses()` devolve `None` quando a economia não supera a
    operação; `payback_dificil_de_aprovar()` sinaliza payback acima de 12 meses.
  - `scores`: `score_prontidao()`, `score_viabilidade()` (pontuação, máximo e faixa do YAML)
    e `nota_prontidao_para_viabilidade()`. Notas fora de 0–3, critério faltando ou
    desconhecido geram erro.
  - `sinais`: `contar_sinais_por_bloco()`, com todos os blocos (inclusive os com 0); id
    repetido conta uma vez; id inexistente gera erro.
  - `faixas`: `classificar()` escolhe a faixa sem nenhum limite escrito no código.
- `scores.prontidao_dados.conversao_para_nota` no YAML: score de dados 0–2 → nota 0,
  3–5 → 1, 6–10 → 2, 11–15 → 3; validado (cobre 0–15, notas 0–3, nunca diminui).
- Teste de referência ponta a ponta do caso Roberto (`tests/dominio/test_caso_roberto.py`):
  15 ocorrências × 4 h = 60 h/mês; score de dados 4 → nota 1; payback 20.000 / (3.000 − 400)
  ≈ 7,7 meses; score final 12 → "Seguir com fase 0"; sinais marcados por bloco
  1 = 1, 2 = 2, 8 = 1, 9 = 1, demais = 0. Hipóteses registradas no teste: custo
  da hora R$ 100, 30 h economizadas por mês, operação de R$ 400 como custo fixo.

### Alterado
- Fixture `questionario_v1` movida para `tests/conftest.py`, compartilhada por todos os testes.
- Especificação: tabela de métricas detalhada com os campos que os cálculos usam.

### Removido
- Campo `peso` dos sinais de alerta (modelo, YAML e especificação): o que importa é a
  contagem de sinais marcados por bloco.

## [0.2.0] — 2026-10-07 — Sprint 1: Questionário

### Adicionado
- `config/questionario_v1.yaml`: transcrição do Modelo de Descoberta com os 10 blocos
  (48 obrigatórias, 34 de aprofundamento, 31 sinais de alerta), notas e tabelas de
  consulta de cada bloco, as 12 seções do relatório (bloco 10), o encerramento (5 itens),
  os 6 tipos de solução da árvore de decisão do bloco 3 e os dois scores com suas faixas
  (prontidão de dados 0–15; viabilidade final 0–18).
- Condicionais de visão computacional: 4 perguntas no bloco 4, exibidas só quando o tipo
  de solução é `visao_computacional`.
- `descoberta.questionario`: modelos Pydantic imutáveis, `carregar_questionario()` e
  `perguntas_visiveis()`.
- Validações: campos desconhecidos, ids únicos, blocos numerados em sequência,
  condicionais citando tipos existentes e só depois do bloco 3, faixas de score
  contíguas cobrindo de 0 ao máximo, blocos de origem existentes e tabelas com todas
  as colunas.
- `QuestionarioInvalido`: erros em português, com o arquivo e o caminho do campo
  (ex.: `blocos[id=processo].perguntas[id=b2.o1].tipo: valor 'obrigatorio' inválido`),
  incluindo a linha e a coluna quando o YAML está mal formado.
- `docs/modelo-descoberta.md` versionado no repositório.

### Alterado
- Dependências `pydantic` e `pyyaml` adicionadas.
- `[tool.uv] python-preference = "only-managed"`: o uv usa apenas o Python que ele
  mesmo instala, nunca o do sistema nem o do Anaconda.

### Pendências para o Sprint 2
- Definir o uso do campo `peso` dos sinais de alerta (hoje é 1 em todos e não entra em
  nenhum cálculo) ou removê-lo do modelo e do YAML.
- Definir a regra de conversão do score de prontidão de dados (0–15) para a nota do
  critério `prontidao_dados` do score final (0–3), validando com o caso Roberto
  (score 4 → nota 1).

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

# Evidências de qualidade (ISO/IEC 25010)

Levantamento do Sprint 8 (14/10/2026, versão 1.0.0): para cada atributo, a característica
correspondente da ISO/IEC 25010:2023, a evidência que já existe no repositório, o que foi
medido agora e o que ainda falta. **É material de apoio:** o texto final, para quem lê
a documentação, fica para o Sprint 9.

Medições em `docs/qualidade/medicoes.json` (gerado por `scripts/medir_desempenho.py`):
Windows 11 Pro, Intel de 16 núcleos, Python 3.13; tempos do servidor, sem a rede e sem o
navegador (p50 = mediana; p95 = 95% dos pedidos abaixo disso).

## Correspondência com a norma

A edição 2023 da ISO/IEC 25010 tem nove características. Os atributos pedidos para este
projeto se distribuem assim:

| Atributo | Na ISO/IEC 25010:2023 |
| --- | --- |
| Corretude | Adequação funcional → corretude funcional |
| Confiabilidade | Confiabilidade (maturidade, disponibilidade, tolerância a falhas, recuperabilidade) |
| Eficiência | Eficiência de desempenho (comportamento no tempo, uso de recursos) |
| Usabilidade | Capacidade de interação (antes, "usabilidade") |
| Manutenibilidade | Manutenibilidade (modularidade, analisabilidade, modificabilidade) |
| Testabilidade | Manutenibilidade → testabilidade |
| Portabilidade | Flexibilidade (antes, "portabilidade") → adaptabilidade, instalabilidade |
| Escalabilidade | Flexibilidade → escalabilidade (nova na edição 2023) |
| Segurança | Segurança (confidencialidade, integridade, autenticidade…) |
| Compatibilidade | Compatibilidade (coexistência, interoperabilidade) |

A característica "proteção" (*safety*, nova em 2023) não se aplica: a app não controla
nada físico.

## Por atributo

### Corretude

- **Já existe:** o caso de referência (Roberto) reproduzido em todas as camadas: cálculos
  (`tests/dominio/test_caso_roberto.py`), banco (`test_caso_roberto_persistido.py`),
  tela, relatório e proposta; cada regra de negócio da especificação tem teste (scores,
  faixas, payback, condicionais do questionário); o relatório usa os mesmos números da
  tela (`dominio.painel`), e um teste de estrutura impede o relatório de refazer contas.
- **Medido agora:** caso Roberto **de ponta a ponta no navegador**, num banco vazio
  (`tests/e2e/test_caso_roberto_ponta_a_ponta.py`): 60 h/mês, 4 de 15, 7,7 meses, 12 de
  18 → seguir com fase 0, na tela e no PDF registrado; validado também numa instalação do
  zero (`validacao-instalacao-limpa.md`). Suíte: **98%** de cobertura de linhas,
  **1.325** testes.
- **Falta:** revisão do relatório e da proposta do Roberto por quem os receberia (Gui);
  cobertura de ramos (`--cov-branch`), para ver condições não exercitadas.

### Confiabilidade

- **Já existe:** salvamento a cada campo, com aviso visível de falha (a tela não finge
  que salvou); versões enviadas com hash SHA-256 do conteúdo e do PDF, conferível no
  rodapé; a app funciona sem internet, e sem LLM o relatório sai por template.
- **Medido agora:** migrações em transação única (um erro no meio desfaz tudo: teste com
  uma migração que falha de propósito), cópia de segurança antes de migrar, e banco
  antigo reconhecido sem perda (125 linhas do `demo.db` iguais e `integrity_check` ok).
- **Falta:** teste manual de queda: fechar a app à força (ou desligar o notebook) no meio
  da sessão e conferir que só o campo em edição se perde; teste de restauração de um
  backup seguindo o README.

### Eficiência

- **Já existe:** nada medido antes deste sprint.
- **Medido agora** (p50 / p95):

  | Operação | p50 | p95 |
  | --- | --- | --- |
  | Abrir a sessão | 4,6 ms | 5,2 ms |
  | Trocar de aba (HTMX) | 3,8 ms | 4,0 ms |
  | Salvar uma resposta | 3,9 ms | 4,7 ms |
  | Salvar um número e recalcular o painel | 5,4 ms | 5,9 ms |
  | Abrir a revisão | 12,3 ms | 13,6 ms |
  | Prévia do relatório | 7,3 ms | 8,3 ms |
  | Relatório em Markdown | 5,8 ms | 7,5 ms |
  | Relatório em PDF (77 KB) | 88,0 ms | 143,3 ms |
  | Relatório em DOCX (50 KB) | 147,9 ms | 156,4 ms |
  | Proposta em PDF | 46,4 ms | 49,1 ms |
  | Relatório + proposta num PDF (137 KB) | 137,8 ms | 140,8 ms |
  | Registrar versão (gera e guarda o PDF) | 93,5 ms | 94,3 ms |
  | Ligar a app (banco novo / em dia / legado) | 85 / 52 / 100 ms | — |

  Pico de memória do Python ao gerar o PDF maior: 1,5 MB além do que a app já usa. Banco
  do caso Roberto completo: 260 KB. Primeira abertura num computador sem nada: 26 s
  (download); depois, 2,4 s.
- **Falta:** tempo percebido no navegador (do clique à tela atualizada), medido com o
  Playwright; memória total do processo (RSS) em uso real; medir num notebook mais
  modesto (a máquina acima é rápida).

### Usabilidade

- **Já existe:** sessão completa conduzida só com o teclado (critério do Sprint 5, teste
  no navegador); atalhos com ajuda (`Ctrl+/`); quadro do que falta preencher; layout
  testado contra sobreposição; números no formato brasileiro; avisos claros de erro.
- **Medido agora:** instalação seguindo só o README, com `iniciar.bat`; mensagens para
  `uv` ausente e porta ocupada.
- **Falta:** a instalação feita por alguém que não programa (Windows Sandbox), com tempo
  e dúvidas anotados; uma sessão real cronometrada (a app atrapalha a conversa?);
  verificação de acessibilidade (contraste, leitor de tela) com uma ferramenta como o
  axe.

### Manutenibilidade

- **Já existe:** arquitetura em camadas com dependências para dentro, garantida por teste
  (`tests/test_estrutura.py`: `dominio` não importa `web`, `repositorio` nem `llm`);
  questionário, modelo de proposta, prompts e configuração do LLM fora do código (YAML e
  Markdown versionados); ruff com regras de estilo, bugs e segurança; pre-commit;
  migrações versionadas, com teste de deriva; CHANGELOG por sprint.
- **Medido agora:** —
- **Falta:** complexidade por função (ruff `C90`, só para medir) e tamanho dos módulos;
  tempo para uma mudança típica (por exemplo, uma pergunta nova no questionário v2).

### Testabilidade

- **Já existe:** TDD em todos os sprints; provedores de LLM falsos (nenhum teste chama a
  API ou a rede: um fixture bloqueia conexões para fora); banco temporário por teste;
  testes no navegador (Playwright) com servidor real; datas injetáveis.
- **Medido agora:** **1.325** testes; suíte completa em cerca de **3 min** nesta máquina
  (4 min com cobertura); no runner Windows do CI, sem o navegador, cerca de 20 min.
  Uma falha intermitente apareceu uma vez, sem registro do teste; em 5 execuções
  completas seguidas (com `-rf` e `--junitxml`), 1.325 passaram em todas, sem nenhuma
  falha (a acompanhar no CI).
- **Falta:** cobertura de ramos; acompanhar a falha intermitente no CI; acelerar a suíte no
  Windows (por exemplo, testes em paralelo).

### Portabilidade

- **Já existe:** Python gerenciado pelo `uv` (não depende do Python do sistema); caminhos
  com `pathlib`; CI no Linux.
- **Medido agora:** job Windows no CI (testes sem navegador); instalação do zero no
  Windows a partir do ZIP; o `iniciar.bat` com finais de linha garantidos pelo
  `.gitattributes`.
- **Falta:** macOS (nenhuma verificação automática); Windows 10.

### Escalabilidade

- **Já existe:** declarada fora do escopo (um usuário, SQLite local; README).
- **Medido agora:** com 500 clientes e 1.000 sessões sintéticas, a lista de clientes abre
  em 6,9 ms (p50) e o detalhe de um cliente em 1,9 ms; o banco ocupa 364 KB.
- **Falta:** nada para o escopo atual. Um volume muito maior (dezenas de milhares de
  sessões) ou uso por equipe pediria outra arquitetura, a tratar no guia de produção.

### Segurança

- **Já existe:** anonimização antes de qualquer envio ao LLM, prévia obrigatória e teste
  de que o pedido HTTP não contém nenhum dado pessoal do demo (critério do Sprint 7);
  chave só em variável de ambiente, nunca exibida (`SecretStr`); `.env` e bancos fora do
  Git, com teste; Claude Code proibido de ler o `.env`.
- **Medido agora:** só `127.0.0.1`/`localhost` (DNS rebinding) e gravação só a partir da
  própria app (CSRF), com testes; regras S do ruff; pip-audit sem vulnerabilidades;
  gitleaks em todo o histórico sem segredos; revisão de dados pessoais no histórico
  (`revisao-historico.md`); Dependabot; actions fixadas por hash; `SECURITY.md`.
- **Falta:** modelo de ameaças e guia de produção (Sprint 9); teste de injeção nos
  documentos gerados (HTML na tela, fórmulas no DOCX); análise estática além do ruff
  (CodeQL, ativável no GitHub depois de público).

### Compatibilidade

- **Já existe:** Chromium nos testes no navegador; DOCX e PDF relidos nos testes
  (python-docx e pypdf); o PDF único junta relatório e proposta mantendo cada rodapé.
- **Medido agora:** —
- **Falta:** abrir o DOCX no Word e no LibreOffice e o PDF no Acrobat e no navegador
  (manual); usar a app no Edge e no Firefox; coexistência: porta ocupada por outro
  programa (já tratada pelo inicializador) e a app aberta duas vezes.

## Resumo do que falta medir

1. Instalação por quem não programa (Windows Sandbox) e uma sessão real cronometrada.
2. Revisão do relatório e da proposta do Roberto (Gui).
3. Tempo percebido no navegador e memória total do processo; medição num notebook
   modesto.
4. Teste manual de queda e de restauração de backup.
5. Cobertura de ramos e complexidade (ruff C90).
6. Documentos no Word, LibreOffice e Acrobat; a app no Edge e no Firefox.
7. Acessibilidade (axe) e teste de injeção nos documentos.

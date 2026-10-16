# Atributos de qualidade (ISO/IEC 25010)

A ISO/IEC 25010 é a norma internacional que define o que é "qualidade de produto de
software": um conjunto de características (corretude, confiabilidade, segurança…) que dá
para avaliar uma a uma. Esta página usa a edição de 2023 como roteiro. Para cada atributo,
mostra **o que garante a qualidade** na app, **o que foi medido** e **o que ainda não foi
verificado**, sem esconder as lacunas.

**De onde vêm os números:** as medições foram feitas em 14/10/2026, na versão 1.0.0
(Sprint 8), num Windows 11 Pro com processador Intel de 16 núcleos e Python 3.13. Os tempos
são do servidor, sem a rede e sem o navegador: p50 é a mediana, e p95 quer dizer que 95%
dos pedidos ficaram abaixo do valor. Os dados brutos estão em
[`medicoes.json`](medicoes.json), gerado por `scripts/medir_desempenho.py`, e podem ser
refeitos em qualquer máquina.

## Correspondência com a norma

A edição de 2023 tem nove características. Os atributos avaliados aqui se distribuem
assim:

| Atributo | Na ISO/IEC 25010:2023 |
| --- | --- |
| Corretude | Adequação funcional → corretude funcional |
| Confiabilidade | Confiabilidade (maturidade, disponibilidade, tolerância a falhas, recuperabilidade) |
| Eficiência | Eficiência de desempenho (comportamento no tempo, uso de recursos) |
| Usabilidade | Capacidade de interação (antes, "usabilidade") |
| Manutenibilidade | Manutenibilidade (modularidade, analisabilidade, modificabilidade) |
| Testabilidade | Manutenibilidade → testabilidade |
| Portabilidade | Flexibilidade (antes, "portabilidade") → adaptabilidade, instalabilidade |
| Escalabilidade | Flexibilidade → escalabilidade (nova na edição de 2023) |
| Segurança | Segurança (confidencialidade, integridade, autenticidade…) |
| Compatibilidade | Compatibilidade (coexistência, interoperabilidade) |

A característica "proteção" (*safety*, nova em 2023) não se aplica: a app não controla
nada físico.

## Por atributo

### Corretude

*Os cálculos e os documentos dão o resultado certo?*

- **O que garante:** cada regra de negócio da especificação tem teste (custo da dor,
  operação, payback, scores, faixas, condicionais). O caso de referência (Roberto) é
  reproduzido em todas as camadas: cálculos (`tests/dominio/test_caso_roberto.py`), banco,
  tela, relatório e proposta. O relatório usa os mesmos números da tela (o painel do
  domínio), e um teste de estrutura impede o relatório de refazer contas.
- **Medido:** o caso Roberto **de ponta a ponta no navegador**, num banco vazio
  (`tests/e2e/test_caso_roberto_ponta_a_ponta.py`): 60 h/mês, score de dados 4 de 15,
  payback de 7,7 meses e score final 12 de 18 → seguir com fase 0, na tela e no PDF
  registrado. Validado também numa instalação do zero
  ([registro](validacao-instalacao-limpa.md)). Cobertura de linhas da suíte: **98%**.
- **Ainda não verificado:** a leitura do relatório e da proposta do Roberto por quem os
  receberia; cobertura de ramos (`--cov-branch`), para achar condições nunca exercitadas.

### Confiabilidade

*A app não perde dados nem finge que salvou?*

- **O que garante:** salvamento a cada campo, com aviso visível de falha (a tela não diz
  "Salvo" se não salvou); versões enviadas guardadas com SHA-256 do conteúdo e do PDF,
  conferível no rodapé; funcionamento sem internet; sem LLM, o relatório sai por template.
- **Medido:** migrações numa transação única (um teste faz uma migração falhar de propósito
  e confere que nada mudou), cópia de segurança antes de migrar, e um banco antigo
  reconhecido sem perda (as 125 linhas do `demo.db` iguais e `integrity_check` ok).
- **Ainda não verificado:** queda no meio da sessão (fechar a app à força ou desligar o
  notebook e conferir que só o campo em edição se perde) e a restauração de um backup
  seguindo o [guia](../guias/backup-e-restauracao.md).

### Eficiência

*A app responde rápido o bastante para não atrapalhar a conversa?*

- **Medido** (p50 / p95):

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

    Pico de memória do Python ao gerar o PDF maior: 1,5 MB além do que a app já usa. O
    banco do caso Roberto completo ocupa 260 KB. A primeira abertura num computador sem
    nada leva 26 s (o download do Python e das bibliotecas); as seguintes, 2,4 s.

- **Ainda não verificado:** o tempo percebido no navegador (do clique à tela atualizada), a
  memória total do processo em uso real e a medição num notebook mais modesto (a máquina
  acima é rápida).

### Usabilidade

*Dá para conduzir a conversa sem a app atrapalhar?*

- **O que garante:** a sessão completa conduzida só com o teclado (teste no navegador);
  atalhos com ajuda (`Ctrl+/`); o quadro do que falta preencher; layout testado contra
  sobreposição; números no formato brasileiro; mensagens de erro em português, dizendo o
  que fazer.
- **Medido:** a instalação seguindo só o README, com o `iniciar.bat`, repetida num
  **Windows Sandbox** novo, sem o `uv` (15/10/2026). O que se aprendeu ali virou ajustes:
  duas opções para instalar o `uv` (o `winget` não existe em todo Windows),
  a janela explicando como encerrar, a app que reconhece quando já está aberta e o aviso
  de `.env.txt`.
- **Ainda não verificado:** a instalação feita por alguém que não programa, anotando o
  tempo e as dúvidas; uma sessão real cronometrada (a app atrapalha a conversa?); e
  acessibilidade (contraste, leitor de tela) com uma ferramenta como o axe.

### Manutenibilidade

*É fácil entender e mudar?*

- **O que garante:** arquitetura em camadas com dependências para dentro, conferida por
  teste (`tests/test_estrutura.py`); questionário, modelo de proposta, prompts e
  configuração do LLM fora do código, em arquivos versionados; ruff com regras de estilo,
  bugs e segurança; pre-commit; migrações versionadas com teste de deriva; CHANGELOG por
  etapa; esta documentação, conferida com o código por `tests/test_documentacao.py`. As
  decisões estão em [Arquitetura e decisões](../explicacao/arquitetura.md).
- **Ainda não verificado:** complexidade por função (ruff `C90`) e o tempo de uma mudança
  típica (por exemplo, uma pergunta nova num questionário v2).

### Testabilidade

*Dá para testar tudo sem depender de rede, de API ou de sorte?*

- **O que garante:** testes escritos antes do código em todas as etapas; provedores de LLM
  falsos (nenhum teste chama a API: um fixture bloqueia conexões para fora); banco
  temporário por teste; testes no navegador (Playwright) com servidor real; datas
  injetáveis.
- **Medido:** 1.325 testes na versão 1.0.0; a suíte completa leva cerca de 3 min na máquina
  acima (4 min com cobertura) e cerca de 20 min no runner Windows do CI, sem o navegador.
  Uma falha intermitente apareceu uma vez, sem registro do teste; em 5 execuções completas
  seguidas, todos os testes passaram.
- **Ainda não verificado:** cobertura de ramos; a origem da falha intermitente (acompanhada
  no CI); por que `tests/relatorio/test_exportar.py` leva cerca de 3,5 min no runner
  Windows (geração de PDF repetida, antivírus do runner ou fixtures que poderiam ser
  compartilhadas).

### Portabilidade

*Instala e roda em outros computadores?*

- **O que garante:** o Python é gerenciado pelo `uv`, e não depende do Python do sistema;
  caminhos com `pathlib`; CI no Linux e no Windows.
- **Medido:** a instalação do zero no Windows a partir do ZIP; o `iniciar.bat` com os finais
  de linha do Windows garantidos pelo `.gitattributes`.
- **Ainda não verificado:** macOS (nenhuma verificação automática) e Windows 10.

### Escalabilidade

*Aguenta o volume de um consultor?*

- **Escopo:** um usuário, com SQLite local. Equipes e servidor estão fora do escopo
  declarado.
- **Medido:** com 500 clientes e 1.000 sessões sintéticas, a lista de clientes abre em
  6,9 ms (p50) e o detalhe de um cliente em 1,9 ms, com o banco em 364 KB.
- **Fora do escopo:** um volume muito maior ou o uso por uma equipe pediria outra
  arquitetura. Veja [Uso em produção](../explicacao/uso-em-producao.md).

### Segurança

*Os dados dos clientes estão protegidos?*

- **O que garante:** anonimização antes de qualquer envio ao LLM, prévia obrigatória e um
  teste que confere que o corpo do pedido HTTP não contém nenhum dado pessoal do demo; a
  chave só em variável de ambiente, nunca exibida; `.env` e bancos fora do Git, com teste;
  só `127.0.0.1`/`localhost` (contra DNS rebinding) e gravação só a partir da própria app
  (contra CSRF), com testes. Detalhes em [Privacidade](../explicacao/privacidade-lgpd.md) e
  no [modelo de ameaças](../explicacao/uso-em-producao.md).
- **Medido:** regras S do ruff (flake8-bandit); `pip-audit` sem vulnerabilidades
  conhecidas; gitleaks em todo o histórico sem segredos; revisão de dados pessoais em todo
  o histórico do Git ([registro](revisao-historico.md)); Dependabot; actions do CI fixadas
  por hash.
- **Ainda não verificado:** teste de injeção nos documentos gerados (HTML na tela, fórmulas
  no DOCX) e análise estática além do ruff (como o CodeQL).

### Compatibilidade

*Funciona junto com o resto do ambiente do consultor?*

- **O que garante:** testes no navegador com o Chromium (a base do Chrome e do Edge); DOCX e
  PDF relidos nos testes (python-docx e pypdf); o PDF único junta relatório e proposta
  mantendo cada rodapé; porta ocupada por outro programa e app aberta duas vezes tratadas
  pelo inicializador.
- **Ainda não verificado:** o DOCX no Word e no LibreOffice e o PDF no Acrobat (abertura
  manual); a app no Edge e no Firefox.

## Resumo do que ainda falta verificar

1. A instalação por quem não programa e uma sessão real cronometrada.
2. A leitura do relatório e da proposta do Roberto por quem os receberia.
3. O tempo percebido no navegador, a memória total do processo e a medição num notebook
   modesto.
4. O teste de queda e o de restauração de backup.
5. Cobertura de ramos e complexidade (ruff `C90`).
6. Os documentos no Word, no LibreOffice e no Acrobat; a app no Edge e no Firefox.
7. Acessibilidade (axe) e teste de injeção nos documentos.

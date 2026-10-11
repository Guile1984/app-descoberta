# Especificação — App de Descoberta para IA

Oct 7, 2026 · @Guilherme Ferraz Stauffer

App local para conduzir ao vivo, no notebook, a sessão de descoberta do Modelo de Descoberta para PMEs e gerar o Relatório de Descoberta com apoio de LLM.

## Visão geral e escopo do MVP

A app digitaliza o Modelo de Descoberta: roteiro guiado durante a reunião, cálculos automáticos e relatório final. Usuário único (consultor), rodando localmente no notebook, funcional sem internet durante a sessão.

**Entra no MVP**

- Cadastro de cliente e abertura de sessão.
- Roteiro guiado bloco a bloco: obrigatórias, aprofundamento e condicionais ativadas pelo tipo de solução (bloco 3).
- Resposta por pergunta, sinais de alerta com um clique e anotações livres.
- Cálculos automáticos: custo da dor, score de dados, custo de operação, payback e score final.
- Relatório de Descoberta por template e rascunho redigido por LLM, ambos exportáveis (Markdown, DOCX, PDF).

**Fica para versões futuras**

- Gravação e transcrição da reunião.
- Vários consultores na mesma conta.
- Proposta comercial gerada a partir do relatório.
- Sugestão automática de sinais de alerta nas respostas.

## Fluxo de uso

A tela principal é feita para anotar ao vivo no notebook, sem travar a conversa.

**Antes da sessão**

1. Cadastrar o cliente (nome, empresa, setor, nº de funcionários, contato).
2. Registrar o contexto prévio.
3. Marcar se a amostra de dados foi recebida.

**Durante a sessão**

1. Layout em duas colunas: perguntas à esquerda; anotações, sinais e cálculos à direita.
2. Blocos em abas, com navegação livre e atalhos de teclado.
3. Obrigatórias em destaque; aprofundamento recolhido.
4. Condicionais aparecem quando o tipo de solução é escolhido no bloco 3.
5. Salvamento automático a cada campo.
6. Cronômetro geral (muda de cor no aviso e no limite da duração-alvo, definidos no questionário) e indicador de obrigatórias pendentes.
7. Cálculos atualizados em tempo real.
8. Roteiro de encerramento com resumo pronto para ler ao cliente.

**Depois da sessão**

1. Revisar e completar respostas.
2. Na área de revisão pós-sessão (página separada da tela ao vivo), preencher as saídas que o relatório usa: matriz de riscos, indicadores de sucesso, escopo do MVP, próximos passos e os textos narrativos. Um quadro mostra o que ainda falta.
3. Gerar o relatório (template ou rascunho por LLM) e revisar.
4. Exportar e enviar ao cliente.

## Modelo de dados

O questionário é um arquivo de configuração versionado (YAML), separado do código. Cada sessão registra a versão usada.

**Catálogo (YAML, validado com Pydantic)**

| Entidade | Campos principais |
| --- | --- |
| Bloco | número, título, objetivo, saída esperada |
| Pergunta | id, bloco, texto, tipo (obrigatória/aprofundamento), condição de exibição |
| Sinal de alerta | id, bloco, texto |
| Score | bloco onde as notas são dadas, critérios, faixas; no score de dados, conversão para a nota do critério do score final que ele alimenta |
| Duração da sessão | minutos do aviso e do limite (o cronômetro muda de cor) |
| Revisão | categorias de risco (as da tabela do bloco 7, mais "outro"); textos narrativos do relatório (id, título, orientação e perguntas de apoio) |

**Banco (SQLite + SQLModel)**

| Entidade | Campos principais |
| --- | --- |
| Cliente | nome, empresa, setor, nº de funcionários, contato |
| Sessão | cliente, data, versão do questionário, tipo de solução, status, contexto prévio, amostra de dados recebida |
| Resposta | sessão, id da pergunta (ou do item do encerramento), texto |
| Sinal marcado | sessão, id do sinal, observação |
| Anotação livre | sessão, bloco (opcional), texto, horário |
| Métricas | sessão, horas por ocorrência, frequência (quantidade e período), custo da hora, horas economizadas por mês, outros ganhos mensais, investimento, custo de operação (chamadas por dia, custo por chamada, custo fixo mensal) |
| Nota de critério | sessão, id do critério, nota (0–3) |
| Cronômetro | sessão, tempo acumulado, rodando desde |
| Risco | sessão, descrição, categoria (id do YAML), probabilidade e impacto (baixo/médio/alto), mitigação |
| Indicador | sessão, nome, camada (negócio/técnica), valor atual, meta, prazo, como medir (texto: não entram em cálculos) |
| Item de escopo | sessão, texto, entra no MVP (sim/não) |
| Próximo passo | sessão, ação, responsável (cliente/consultor), prazo (data) |
| Texto de seção | sessão, id do texto (do YAML), texto |
| Relatório | sessão, origem (template/LLM), conteúdo, modelo, versão do prompt, data |

Um cliente tem várias sessões; uma sessão tem muitas respostas, sinais e anotações, e um conjunto de métricas. Métricas ficam em campos numéricos próprios, nunca extraídas do texto.

## Stack e arquitetura

FastAPI + HTMX com SQLite, rodando localmente. Escolhida por manter Python quase de ponta a ponta e permitir salvamento a cada campo, o que o Streamlit faz mal.

| Camada | Tecnologia | Responsabilidade |
| --- | --- | --- |
| questionario | Pydantic + YAML | Carregar e validar o catálogo; resolver condicionais |
| dominio | Python puro | Cálculos e regras, sem dependência de banco ou web |
| repositorio | SQLModel + SQLite | Persistência |
| relatorio | Jinja2 + exportadores | Relatório por template; Markdown, DOCX, PDF |
| llm | Cliente abstrato | Provedor (API Claude ou modelo local), anonimização, prompts versionados |
| web | FastAPI + Jinja2 + HTMX | Rotas, telas e atalhos de teclado (JS mínimo) |

Dependências apontam para dentro: `web` usa `dominio`, nunca o contrário. Ferramentas: uv, ruff, pytest (com cobertura), pre-commit.

## Uso de LLM

O LLM atua só depois da sessão, para redigir o rascunho do relatório, que o consultor revisa antes de enviar. Cálculos e condicionais nunca passam pelo LLM.

- **Anonimização:** antes do envio à API, nomes, CPFs, telefones, e-mails e endereços viram marcadores (\[CLIENTE\], \[PESSOA\_1\]); a substituição é desfeita localmente na resposta.
- **Abstração de provedor:** interface única com implementações para a API Claude e para modelo local (Ollama), escolhidas por configuração.
- **Prompts versionados:** arquivos de prompt no repositório; cada relatório guarda modelo e versão do prompt.
- **Falha segura:** sem internet ou com erro na API, a app oferece o relatório por template.
- **Segredos:** chave de API apenas em variável de ambiente (.env fora do Git).

## Sprints

Ordem do núcleo para a interface. Cada sprint só fecha com todos os critérios de aceite atendidos.

| Sprint | Entrega | Critério de aceite |
| --- | --- | --- |
| 0 — Setup | Repositório, uv, ruff, pytest, pre-commit, estrutura de pastas | `uv run pytest` e `ruff check` passam em projeto vazio |
| 1 — Questionário | YAML com 10 blocos + encerramento; modelos Pydantic; condicionais | YAML inválido gera erro claro; condicionais de visão computacional testadas |
| 2 — Cálculos | Custo da dor, score de dados, custo de operação, payback, score final | Caso Roberto reproduzido: 60 h/mês; score de dados 4; payback ≈ 7,7 meses; score final 12 |
| 3 — Persistência | Entidades SQLModel e repositório | CRUD testado em banco temporário |
| 4 — Web básica | Cliente, sessão, abas por bloco, salvamento automático | Resposta salva sem recarregar a página |
| 5 — Uso ao vivo | Sinais com um clique, anotações, atalhos, cronômetro, cálculos ao vivo | Sessão completa conduzida só com teclado |
| 6a — Saídas estruturadas | Revisão pós-sessão: matriz de riscos (com visualização 3×3), indicadores de sucesso, escopo do MVP, próximos passos e textos narrativos editáveis, com indicação do que falta | Caso Roberto com todas as saídas preenchidas e nenhuma pendência na revisão |
| 6b — Relatório | Relatório por template em versão cliente e versão interna, anexos, memória de cálculo e termo de ciência; exportação Markdown, DOCX, PDF. Usa `dominio.painel` (os mesmos números da tela) e ignora respostas de condicionais ocultas | Relatório do caso Roberto gerado offline |
| 7 — LLM | Provedor abstrato, anonimização, prompts versionados; rascunhos sugeridos para os textos narrativos da revisão | Nenhum dado pessoal no payload enviado (teste automatizado) |
| 8 — Validação | Caso Roberto de ponta a ponta; README; ajustes | Sessão simulada completa e relatório revisado |

## Modo de desenvolvimento

O Claude Code implementa de ponta a ponta; Gui atua como dono do produto e revisor.

**Ciclo de cada sprint**

1. Claude Code propõe o plano do sprint em modo de planejamento.
2. Gui aprova ou ajusta o plano.
3. Claude Code escreve os testes primeiro, depois a implementação.
4. Claude Code roda testes e ruff até passarem.
5. Gui revisa o diff, roda a app e confere o critério de aceite.
6. Commit e atualização do CHANGELOG.

**Papel do Gui**

- Aprovar planos e decisões de arquitetura.
- Validar a app rodando, especialmente a experiência ao vivo (sprints 4 e 5).
- Manter o YAML do questionário alinhado ao Modelo de Descoberta.
- Entender cada camada o suficiente para explicá-la numa entrevista.

**Transparência no portfólio:** o README informa que o projeto foi desenvolvido com Claude Code sob direção e revisão do autor. Desenvolvimento assistido por IA bem conduzido é, por si só, uma competência demonstrável.

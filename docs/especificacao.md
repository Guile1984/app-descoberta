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
- Proposta Comercial como documento separado, a partir da sessão e da revisão, com Condições Gerais editáveis (Sprint 6c).

**Fica para versões futuras**

- Gravação e transcrição da reunião.
- Vários consultores na mesma conta.
- Inclusão de cláusulas extras numa proposta (hoje: ajustar o texto e excluir as removíveis).
- Sugestão automática de sinais de alerta nas respostas.

## Fluxo de uso

A tela principal é feita para anotar ao vivo no notebook, sem travar a conversa.

**Primeiro uso**

1. Preencher o perfil do consultor (nome, empresa, CPF ou CNPJ, contato, cidade/UF e logotipo opcional). Ele vai em todos os documentos, inclusive no bloco de assinatura do consultor, e fica só no banco local.

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
3. Marcar na revisão quais números são hipóteses do consultor (o relatório os destaca).
4. Se quiser, pedir ao LLM rascunhos dos textos narrativos da revisão (e, na proposta, do contexto e do objetivo das fases): o rascunho fica ao lado do texto e só o substitui se o consultor aceitar. Antes do primeiro, conferir a lista de pessoas citadas e a prévia do que sai.
5. Conferir a prévia do relatório (versão cliente e versão interna) e baixar em Markdown, Word ou PDF.
6. Registrar a versão enviada: o PDF fica guardado com número de versão, data e hash SHA-256, que aparecem no rodapé de cada página para conferir a cópia assinada.
7. Criar a Proposta Comercial, como cópia do modelo da proposta e da revisão (escopo, exclusões, hipóteses, passos do cliente). Se o score final indicar "não seguir agora", a app avisa antes e só cria com confirmação.
8. Editar a proposta (contexto, fases, escopo, entregáveis, condições, Condições Gerais), registrar a versão enviada (numeração própria, com hash no rodapé e as cláusulas congeladas) e, se quiser, baixar relatório e proposta num PDF só.

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
| Seção do relatório | id, título; blocos cujas respostas entram na seção, outras respostas e tabelas de referência |

**Modelo da proposta (`config/proposta_v{n}.yaml`, validado com Pydantic e conferido com o questionário)**

| Entidade | Campos principais |
| --- | --- |
| Modelo | versão, título, aviso de que é ponto de partida a revisar com advogado, faixas do score final que pedem alerta, critério de aceite (texto do aceite das entregas, texto das metas de negócio e tabela de referência) |
| Padrão | validade, pagamento, impostos, reajuste, fases (nome, objetivo, duração, escopo, entregáveis, se recebe o escopo e o investimento da sessão, faixas do score em que entra), premissas, responsabilidades do cliente |
| Cláusula | id, título, texto com marcadores de uma lista fechada ({cliente.empresa}, {consultor.empresa}, {consultor.nome}, {foro}), removível |

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
| Hipótese | sessão, campo da métrica assumido pelo consultor |
| Versão do relatório | sessão, número, tipo (cliente/interna), emissão, Markdown canônico, hash do conteúdo, PDF, hash do PDF |
| Relatório | sessão, origem (template/LLM), conteúdo, modelo, versão do prompt, data |
| Perfil do consultor | nome, empresa, CPF/CNPJ (conferido), e-mail, telefone, cidade/UF, logotipo (PNG sem metadados), dados fictícios (demo) |
| Proposta | sessão, versão do modelo, dados do cliente (CPF/CNPJ, representante, cargo, e-mail, cidade/UF), pagamento, impostos, reajuste, validade, criada apesar do alerta |
| Fase da proposta | sessão, nome, objetivo, duração (semanas), investimento |
| Item da proposta | sessão, tipo (escopo, entregável, exclusão, premissa, responsabilidade), fase (escopo e entregáveis), texto |
| Cláusula da proposta | sessão, id da cláusula, texto ajustado, excluída |
| Versão da proposta | sessão, número, emissão, Markdown canônico, hash do conteúdo, PDF, hash do PDF, versão do modelo, Condições Gerais congeladas |
| Texto da proposta | sessão, campo ("contexto"), texto |
| Rascunho | sessão, destino (revisão/proposta), campo, texto, provedor, modelo, versão do prompt, alertas, com anotações internas, situação (pendente/aceito/descartado/substituído), datas |
| Pessoa citada | sessão, nome (trocado por marcador antes do LLM) |
| Prévia do LLM | sessão, impressão (sha256) dos dados conhecidos, confirmada em |

Um cliente tem várias sessões; uma sessão tem muitas respostas, sinais e anotações, e um conjunto de métricas. Métricas ficam em campos numéricos próprios, nunca extraídas do texto.

## Stack e arquitetura

FastAPI + HTMX com SQLite, rodando localmente. Escolhida por manter Python quase de ponta a ponta e permitir salvamento a cada campo, o que o Streamlit faz mal.

| Camada | Tecnologia | Responsabilidade |
| --- | --- | --- |
| questionario | Pydantic + YAML | Carregar e validar o catálogo; resolver condicionais |
| proposta | Pydantic + YAML | Carregar e validar o modelo da proposta; conteúdo inicial e cláusulas efetivas |
| dominio | Python puro | Cálculos e regras, sem dependência de banco ou web |
| repositorio | SQLModel + SQLite | Persistência |
| relatorio | Python puro + python-docx + ReportLab + pypdf | Monta o relatório e a proposta como documentos neutros (blocos) e exporta para Markdown, DOCX e PDF (e os dois num PDF só); os números vêm do Painel do domínio |
| llm | Cliente abstrato | Provedor (API Claude ou modelo local), anonimização, prompts versionados |
| web | FastAPI + Jinja2 + HTMX | Rotas, telas e atalhos de teclado (JS mínimo) |

Dependências apontam para dentro: `web` usa `dominio`, nunca o contrário. Ferramentas: uv, ruff, pytest (com cobertura), pre-commit.

**Exportação offline no Windows:** só bibliotecas que instalam com `uv sync`, sem programas externos. DOCX com python-docx (MIT); PDF com ReportLab (BSD, Python puro), com a fonte DejaVu Sans embutida para caracteres como "≥" e "→". WeasyPrint (exige GTK), pandoc, wkhtmltopdf e LibreOffice foram descartados. Para juntar relatório e proposta num PDF só, pypdf (BSD, Python puro): as páginas são copiadas como estão, e cada parte mantém rodapé, versão e hash. O logotipo do consultor é conferido e regravado com Pillow (licença HPND, que já vinha com o ReportLab).

## Uso de LLM

O LLM atua só depois da sessão, para redigir o rascunho do relatório, que o consultor revisa antes de enviar. Cálculos e condicionais nunca passam pelo LLM.

- **Anonimização:** antes do envio, nomes, CPFs, CNPJs, telefones, e-mails, CEPs, endereços e cidades viram marcadores (\[CLIENTE\], \[PESSOA\_1\]); a substituição é desfeita localmente na resposta. Vale também para os dados do perfil do consultor, para os dados do cliente na proposta e para a lista de pessoas citadas da sessão (a app sugere os nomes). Uma conferência final impede o envio se algo ainda parecer dado pessoal.
- **Prévia obrigatória:** antes do primeiro rascunho, o consultor vê o pedido exato e confirma; a confirmação vale enquanto os dados conhecidos não mudam.
- **Contexto como na versão cliente:** anotações do consultor e sinais de alerta só vão no pedido se o consultor ligar "usar anotações internas como contexto".
- **Rascunhos à parte:** cada sugestão fica numa tabela própria (provedor, modelo, versão do prompt) e só substitui o texto do consultor quando ele aceita.
- **Nunca ao vivo:** com o cronômetro da sessão rodando, a app recusa gerar rascunhos.
- **Abstração de provedor:** interface única com implementações para a API Claude e para modelo local (Ollama), escolhidas por configuração.
- **Prompts versionados:** arquivos `prompts/<id>_v<n>.md` no repositório, conferidos ao carregar; cada rascunho guarda o modelo e a versão do prompt.
- **Falha segura:** sem internet, sem chave ou com erro na API (ou recusa do modelo, sem reenvio para outro), a app avisa e mantém o texto atual e o relatório por template.
- **Segredos:** chave de API apenas em variável de ambiente (.env fora do Git); provedor escolhido por `config/llm.yaml` ou `DESCOBERTA_LLM_PROVEDOR`, desligado por padrão; testes sem nenhuma chamada real.

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
| 6b — Relatório | Relatório por template em versão cliente e versão interna (com sinais de alerta e anotações), capa, 12 seções, Anexo A (respostas), Anexo B (memória de cálculo com hipóteses destacadas) e termo de ciência e validação; exportação Markdown, DOCX, PDF; registro das versões enviadas com hash no rodapé. Usa `dominio.painel` (os mesmos números da tela) e ignora respostas de condicionais ocultas | Relatório do caso Roberto gerado offline nos três formatos |
| 6c — Proposta comercial | Perfil do consultor (primeiro uso); Proposta Comercial separada do relatório, a partir da sessão e da revisão; Condições Gerais num modelo editável fora do código, com ajuste e exclusão por proposta; versões registradas com hash e cláusulas congeladas; aviso antes de propor com score "não seguir agora"; relatório e proposta num PDF só; títulos que não ficam sozinhos no pé da página | Proposta do caso Roberto gerada offline nos três formatos e registrada, sem alterar o relatório |
| 7 — LLM | Provedor abstrato (API Claude e Ollama), anonimização com lista de pessoas citadas e prévia obrigatória, prompts versionados; rascunhos sugeridos para os textos narrativos da revisão e da proposta, numa tabela própria | Nenhum dado pessoal no payload enviado (teste automatizado) |
| 8 — Validação e lançamento | Caso Roberto de ponta a ponta; escolha de licença; README para quem não programa, com GIF de demonstração; transparência sobre o desenvolvimento com Claude Code; limitações declaradas; SECURITY.md; aviso de uso local; verificações de segurança no CI; revisão de dados e segredos no histórico do Git; repositório público | Sessão simulada completa, relatório revisado e repositório público sem dados pessoais nem segredos no histórico |
| 9 — Documentação | Documentação no modelo Diátaxis (tutorial, guias práticos, referência e explicação, incluindo a metodologia do Modelo de Descoberta); site com MkDocs e tema Material no GitHub Pages; guia de uso em produção com modelo de ameaças; CONTRIBUTING; CI da documentação | Site publicado, compilando sem avisos e sem links quebrados |

### Sprint 6c — Proposta comercial

- A proposta é um documento separado do relatório: renegociar (novas versões da proposta) nunca altera o relatório nem as versões dele.
- O modelo (`config/proposta_v1.yaml`) traz o aviso de que é ponto de partida e deve ser revisado por advogado; o aviso aparece para o consultor na tela e não vai ao documento do cliente.
- Condições Gerais no anexo final, cobertas pela mesma assinatura e pelo mesmo hash. Foro, prevalência do contrato detalhado, confidencialidade, LGPD e limitação de responsabilidade não podem ser excluídas de uma proposta.
- Ao registrar uma versão, o texto impresso das cláusulas fica congelado com ela.

### Sprint 7 — LLM

- O LLM só sugere: os rascunhos ficam numa tabela própria e o consultor aceita ou descarta. Cálculos e condicionais nunca passam pelo LLM; os números vão prontos do Painel.
- Provedor desligado por padrão; API Claude (`claude-opus-5-5`) ou Ollama local, escolhidos por configuração. Recusa do modelo vira aviso, sem reenvio.
- Os rascunhos são para textos que o cliente lê: o contexto segue a versão cliente do relatório (sem anotações e sinais, a não ser por escolha do consultor).
- Critério de aceite: o caso Roberto inteiro passa pelo SDK real com transporte falso, e o corpo de cada pedido HTTP é conferido contra todos os dados pessoais do demo.

### Sprint 8 — Validação e lançamento

- Caso Roberto de ponta a ponta: sessão simulada, revisão, relatório e versão registrada.
- Escolha da licença do projeto (e conferência das licenças das dependências e da fonte DejaVu).
- README para quem não programa: o que a app faz, como instalar e usar, com um GIF de demonstração.
- Transparência: o projeto foi desenvolvido com Claude Code, sob direção e revisão do autor.
- Limitações declaradas (o que a app não faz e os cuidados de uso).
- `SECURITY.md`: política de relato de vulnerabilidades e escopo suportado.
- Aviso no README: a app é projetada para uso local, por um único usuário, e não deve ser exposta à rede sem as medidas do guia de produção (Sprint 9).
- Verificações de segurança no CI: `pip-audit` (dependências com vulnerabilidades conhecidas), regras "S" do ruff (flake8-bandit), gitleaks (segredos no repositório e no histórico) e Dependabot (atualizações de dependências).
- Revisão de dados pessoais e segredos em todo o histórico do Git antes de tornar o repositório público.
- Repositório público.
- Migrações do banco com Alembic (antecipadas do guia de produção): o esquema do fim do Sprint 7 é a revisão inicial; bancos anteriores (como o `data/demo.db`) são reconhecidos sem perda de dados; a app migra ao ligar, com cópia de segurança antes e tudo numa transação.
- Proteções para o uso local: só os hosts `127.0.0.1` e `localhost` (contra DNS rebinding) e pedidos que gravam dados só vindos da própria app (contra CSRF a partir de outra aba do navegador). Início com dois cliques (`iniciar.bat`), sempre em `127.0.0.1`.
- Licenças: código em MIT; metodologia (`docs/modelo-descoberta.md` e conteúdo do questionário) em CC BY 4.0; avisos de terceiros em `THIRD_PARTY_NOTICES.md`, conferidos por teste.
- Evidências de qualidade com base na ISO/IEC 25010 (`docs/qualidade/`), com medições de tempo de resposta e de geração de documentos; o texto final fica para o Sprint 9.

### Sprint 9 — Documentação

- Documentação no modelo Diátaxis:
  - tutorial: a primeira sessão de descoberta com a app, do cadastro ao relatório;
  - guias práticos: tarefas específicas (ex.: criar uma nova versão do questionário, fazer backup);
  - referência: questionário YAML, cálculos, estrutura do relatório, comandos;
  - explicação: a metodologia do Modelo de Descoberta, as decisões de arquitetura e o uso de LLM.
- Site com MkDocs e tema Material, publicado no GitHub Pages.
- Guia de uso em produção, com modelo de ameaças e a lista de medidas necessárias antes de expor a app: autenticação, HTTPS, proteção contra CSRF, limite de requisições, criptografia do banco e dos backups, logs de auditoria e teste de intrusão profissional (as migrações com Alembic já existem desde o Sprint 8).
- `CONTRIBUTING.md`.
- CI da documentação: compilação do site (modo estrito) e verificação de links quebrados.

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

# Modelo de Descoberta — Apps de IA para PMEs

> © 2026 Guilherme Ferraz Stauffer. Licenciado sob [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br):
> pode ser usado e adaptado, inclusive comercialmente, com crédito ao autor. Veja
> `LICENSE-METODOLOGIA.md`.

## Como usar o modelo

A sessão de descoberta responde três perguntas antes de qualquer proposta: a dor é real, a IA é o caminho certo e os dados permitem fazê-la. O modelo é voltado a PMEs, onde quem decide costuma ser o dono, os dados vivem em planilhas, WhatsApp e ERP básico, o orçamento é curto e raramente há equipe de TI.

- **Duração-alvo:** 60 a 90 minutos, com o decisor presente.
- **Perguntas obrigatórias:** feitas em toda sessão.
- **Perguntas de aprofundamento:** usadas quando o tempo permite ou a resposta obrigatória ficou vaga.
- **Sinais de alerta:** anotados durante a conversa; alimentam o score final.
- **Saída de cada bloco:** o que precisa estar registrado antes de passar ao próximo.
- **Linguagem:** de negócio, nunca técnica. A tradução para requisitos técnicos é trabalho seu, depois da sessão.
- **Perguntas condicionais:** o bloco 3 define o tipo de solução, e isso abre perguntas específicas nos blocos seguintes (ex.: RAG abre perguntas sobre documentos; previsão abre perguntas sobre séries históricas).

Antes da sessão, peça ao cliente uma amostra dos dados. Depois dela, entregue o Relatório de Descoberta (bloco 10) em até 48 h.

## Bloco 1 — Problema de negócio

O objetivo é sair com uma dor nomeada, medida e com dono.

**Obrigatórias**

1. Qual tarefa ou situação mais toma tempo ou dinheiro da empresa hoje?
2. Com que frequência isso acontece (por dia ou por semana)?
3. Quantas pessoas se envolvem e quanto tempo cada uma gasta?
4. O que acontece quando dá errado? (cliente perdido, retrabalho, multa, atraso)
5. Se isso estivesse resolvido daqui a 6 meses, o que mudaria concretamente?
6. Quem decide sobre o investimento e quem vai usar a solução no dia a dia?
7. Quem mais conhece esse processo a fundo e precisa participar da próxima conversa?

**Aprofundamento**

- Já tentaram resolver antes? Com o quê, e por que não funcionou?
- Isso afeta o faturamento diretamente ou só o custo operacional?
- Existe sazonalidade, com picos em certos meses?
- Algum concorrente já resolve isso melhor?

**Sinais de alerta**

- O cliente quer "usar IA" sem conseguir nomear uma dor específica.
- A dor acontece poucas vezes por mês, o que torna o retorno improvável.
- Quem decide não está presente na sessão.
- A expectativa é de 100% de acerto ou zero intervenção humana.

**Saída do bloco**

Frase-problema: *"Hoje [quem] gasta [quanto] fazendo [o quê], o que causa [impacto]. O sucesso será [métrica] em [prazo]."* Com as perguntas 2 a 4, estime o custo mensal da dor; ele é o teto do orçamento razoável.

## Bloco 2 — Processo atual × futuro

O objetivo é desenhar como a tarefa é feita hoje e onde a IA entraria.

**Obrigatórias**

1. Descreva passo a passo como a tarefa é feita hoje, do início ao fim.
2. Quais ferramentas são usadas em cada passo? (planilha, ERP, WhatsApp, papel)
3. Em qual passo há mais demora, erro ou retrabalho?
4. Quais decisões são tomadas no processo, e com base em quê? (experiência, regra, tabela)
5. O que pode ser automatizado e o que precisa continuar com uma pessoa?

**Aprofundamento**

- O processo é igual para todos os funcionários ou cada um faz do seu jeito?
- Existe alguma regra documentada, ou ela está "na cabeça" de alguém?
- Quem seria afetado por mudanças? Há resistência prevista da equipe?

**Sinais de alerta**

- Ninguém descreve o processo de forma consistente: primeiro padronizar, depois automatizar.
- O conhecimento está concentrado em uma pessoa que não participa da sessão.
- O passo problemático depende de informação que não é registrada em lugar nenhum.

**Saída do bloco**

Fluxograma *as-is* e *to-be*, marcando onde a IA entra e onde fica a revisão humana. Se o passo crítico for uma decisão por regra fixa, o bloco 3 tende a indicar automação sem IA.

## Bloco 3 — Adequação de IA

O objetivo é decidir se o projeto usa IA e de que tipo. "Não precisa de IA" é uma resposta válida e gera confiança.

**Obrigatórias**

1. A decisão ou tarefa segue regras claras que alguém conseguiria escrever? ("se X, então Y")
2. Existe histórico de casos passados com o resultado conhecido? (ex.: pedidos aprovados/recusados, peças boas/defeituosas)
3. Qual é o insumo principal: números/tabelas, textos/documentos, imagens, áudio?
4. Um erro da IA é aceitável se for raro? Qual o pior erro possível?
5. A empresa precisa explicar por que a decisão foi tomada? (cliente, fiscal, órgão regulador)

**Aprofundamento**

- Uma pessoa experiente acerta quanto? Isso vira a meta realista para a IA.
- A tarefa muda com frequência (regras, produtos, preços)?
- O resultado precisa sair na hora ou pode levar minutos/horas?

**Árvore de decisão**

| Situação | Caminho indicado |
| --- | --- |
| Regras claras e estáveis | Automação tradicional, sem IA |
| Tabelas + histórico com resultado | ML clássico (classificação/previsão) |
| Documentos, e-mails, perguntas frequentes | LLM com RAG |
| Imagens ou vídeo | Visão computacional |
| Tarefa com várias etapas e ferramentas | Agente com LLM |
| Sem histórico e sem regras | Coletar dados primeiro, sem IA ainda |

**Sinais de alerta**

- Erro inaceitável e sem possibilidade de revisão humana.
- Exigência de explicação total, com caminho pensado em caixa-preta (deep learning ou LLM).
- Expectativa de que a IA "descubra sozinha" o que fazer, sem exemplos.

**Saída do bloco**

Tipo de solução, baseline (como seria resolvido sem IA ou por um humano) e justificativa curta. Se o caminho for "sem IA", a sessão continua com escopo de automação.

## Bloco 4 — Dados

O objetivo é medir quanto falta para os dados serem usáveis. Em PMEs, o dado quase sempre existe, mas espalhado ou incompleto.

**Obrigatórias**

1. Onde os dados dessa tarefa ficam hoje? (ERP, planilhas, e-mail, WhatsApp, pastas, papel)
2. Há quanto tempo vocês registram isso? Quantos casos existem, mais ou menos?
3. O resultado de cada caso também foi registrado? (ex.: "a fissura era grave", "o cliente pagou")
4. Quem tem acesso e quem é o dono desses dados? É possível exportá-los?
5. Há dados pessoais de clientes ou funcionários? (CPF, telefone, saúde, salário)

**Aprofundamento**

- Os dados seguem um padrão ou cada pessoa preenche de um jeito?
- Há muitos campos vazios, duplicados ou com erro de digitação?
- Novos dados continuarão chegando depois da entrega? Em que volume?
- Existe algum dado que deveria ser coletado e não é?
- Podem enviar uma amostra antes da próxima reunião?

**Score de prontidão de dados** (0 a 3 por critério)

| Critério | 0 | 3 |
| --- | --- | --- |
| Disponibilidade | Não existe | Exportável hoje |
| Volume | Dezenas de casos | Milhares de casos |
| Rótulos / resultado | Ausente | Registrado em todos |
| Qualidade | Caótica | Padronizada |
| Acesso legal (LGPD) | Incerto | Base legal clara |

Abaixo de 6: começar por organizar e coletar dados. De 6 a 10: MVP com ressalvas. Acima de 10: pronto para modelar.

**Condicional — visão computacional** (quando o bloco 3 indicar imagens ou vídeo)

- Quem tira as fotos e com qual aparelho?
- Existe padrão de distância, ângulo e iluminação, ou cada um fotografa de um jeito?
- As fotos têm referência de escala (régua, fissurômetro, objeto conhecido)?
- Em que formato e resolução as imagens ficam guardadas?

Sem padrão de captura, a fase 0 inclui um protocolo simples de fotografia antes de qualquer treinamento de modelo.

**Sinais de alerta**

- "Temos muitos dados", mas ninguém sabe dizer onde estão.
- Dados de terceiros sem autorização de uso.
- Rótulos dependem de alguém revisar milhares de casos manualmente.
- Dados pessoais sensíveis sem consentimento ou base legal.

**Saída do bloco**

Inventário de fontes, score de prontidão e, se o score for baixo, uma fase 0 de estruturação de dados no escopo. Peça a amostra antes de enviar a proposta comercial.

## Bloco 5 — Critérios de sucesso

O objetivo é transformar "quero que funcione bem" em números combinados antes do desenvolvimento.

**Obrigatórias**

1. Qual número do negócio precisa mudar? (horas gastas, custo, prazo, taxa de erro, faturamento)
2. Qual o valor atual desse número e qual a meta?
3. Em quanto tempo após a entrega vocês esperam ver o resultado?
4. Qual erro é pior: a IA deixar passar um problema real, ou apontar um problema que não existe?
5. Quem confere o resultado da IA antes de virar ação, e por quanto tempo?

**Aprofundamento**

- Quanto custa, em reais, cada tipo de erro?
- Um acerto parecido com o de um funcionário experiente já é suficiente?
- Como vão medir o resultado na prática? Quem vai acompanhar?

**Duas camadas de métricas**

| Camada | Exemplo (fissuras em concreto) | Quem entende |
| --- | --- | --- |
| Negócio | Reduzir a inspeção de 8 h para 2 h por obra | Dono da PME |
| Técnica | Recall ≥ 95% para fissuras graves | Desenvolvedor |

A pergunta 4 liga as duas camadas. Se deixar passar um caso real é pior, priorize recall; se o alarme falso custa caro, priorize precisão.

**Critério de aceite em três fases**

1. Teste com dados históricos: a métrica técnica atinge a meta?
2. Piloto assistido (2 a 4 semanas): a IA roda em paralelo ao processo atual e uma pessoa compara os resultados.
3. Produção: a métrica de negócio é acompanhada mensalmente.

**Sinais de alerta**

- Meta de 100% de acerto.
- O cliente não sabe o valor atual do indicador, então não há como provar a melhora.
- Ninguém assume a revisão durante o piloto.

**Saída do bloco**

Tabela "indicador atual → meta → prazo → como medir" e critério de aceite assinado pelo cliente.

## Bloco 6 — Requisitos não funcionais

O objetivo é traduzir o dia a dia do cliente em requisitos técnicos e estimar o custo mensal de operação.

**Obrigatórias**

1. Onde a solução será usada? (computador no escritório, celular em campo, tablet)
2. Há internet estável no local de uso?
3. Quantas pessoas vão usar, e quantas vezes por dia?
4. O resultado precisa sair em segundos, ou pode levar alguns minutos?
5. Se o sistema ficar fora do ar por algumas horas, o que acontece?
6. Quanto a empresa aceita pagar por mês para manter a solução funcionando?

**Aprofundamento**

- O uso é constante ou concentrado em certos horários e dias?
- Os usuários têm familiaridade com tecnologia, ou a interface precisa ser muito simples?
- Haverá crescimento de uso no próximo ano? (novas filiais, novos clientes)
- Precisa funcionar em outro idioma?

**Tradução para requisitos técnicos**

| Resposta do cliente | Requisito técnico |
| --- | --- |
| "Uso no canteiro, sem sinal" | Modo offline / modelo embarcado no celular |
| "Resposta na hora" | Latência < 2 s, inferência otimizada |
| "Pode ficar fora por um dia" | Disponibilidade simples, sem redundância cara |
| "50 usuários, 200 análises/dia" | Dimensionamento de servidor ou de cota de API |
| "Até R$ 300/mês" | Teto de custo de nuvem + API |

Em soluções com LLM, cada consulta tem custo. Estime ainda na sessão: volume diário × custo por chamada × 22 dias úteis, e compare com a resposta da pergunta 6.

**Sinais de alerta**

- Exigência de tempo real em local sem internet, com modelo pesado.
- Orçamento mensal menor que o custo estimado de operação.
- Disponibilidade 24/7 exigida, sem orçamento compatível.

**Saída do bloco**

Lista de requisitos não funcionais com valores concretos e custo mensal estimado de operação, para comparar com o custo da dor do bloco 1.

## Bloco 7 — Riscos e compliance

O objetivo é mapear riscos legais, éticos e de segurança e definir mitigações antes do início do projeto.

**Obrigatórias**

1. A solução vai lidar com dados pessoais? De clientes, funcionários ou terceiros?
2. A empresa tem alguém responsável pela LGPD (encarregado/DPO), mesmo que informal?
3. A decisão da IA afeta pessoas diretamente? (crédito, contratação, preço, segurança)
4. O setor tem regulação específica? (saúde, financeiro, engenharia, alimentos)
5. Quem responde legalmente se a IA errar?

**Aprofundamento**

- Os dados podem ser processados fora do Brasil? (APIs de LLM costumam rodar no exterior)
- Há informações confidenciais do negócio que não podem sair da empresa?
- Algum grupo pode ser prejudicado por padrões nos dados históricos?
- A empresa já sofreu vazamento ou incidente de segurança?

**Principais riscos**

| Risco | Exemplo | Mitigação típica |
| --- | --- | --- |
| LGPD | CPF enviado a uma API externa | Anonimizar, base legal, contrato com o fornecedor |
| Viés | Modelo de crédito que penaliza um bairro | Auditoria dos dados e dos resultados por grupo |
| Explicabilidade | Cliente pergunta por que foi recusado | Modelo interpretável ou justificativa registrada |
| Responsabilidade técnica | Laudo estrutural baseado na IA | IA como apoio; decisão final com engenheiro e ART |
| Segurança | Prompt injection, vazamento de dados | Controle de acesso, validação de entradas, logs |
| Dependência de fornecedor | API muda preço ou sai do ar | Camada de abstração, modelo alternativo |

Classifique cada risco por probabilidade e impacto (baixo/médio/alto). Riscos altos nos dois eixos exigem mitigação definida antes do início. Acompanhe também a regulação de IA no Brasil (PL 2338/2023).

**Sinais de alerta**

- Dados sensíveis (saúde, biometria) sem base legal clara.
- Decisão automatizada sobre pessoas, sem revisão humana.
- O cliente quer que a IA assuma a responsabilidade técnica.

**Saída do bloco**

Matriz de riscos com mitigações e cláusula de limites de responsabilidade para a proposta.

## Bloco 8 — Integração e infraestrutura

O objetivo é definir de onde a IA lê os dados e onde entrega o resultado. Se o funcionário precisar abrir mais um sistema, a adoção cai.

**Obrigatórias**

1. Quais sistemas a empresa usa hoje? (ERP, CRM, planilhas, Google Workspace, Microsoft 365, WhatsApp)
2. Onde o resultado da IA precisa aparecer? (no ERP, por WhatsApp, por e-mail, num painel)
3. Quem cuida da tecnologia da empresa? Alguém interno, um fornecedor, ou ninguém?
4. Vocês têm acesso de administrador aos sistemas, ou depende de um fornecedor?
5. Há preferência por nuvem ou por servidor na própria empresa?

**Aprofundamento**

- O ERP permite integração por API? O fornecedor cobra por isso?
- Os dados chegam em tempo real ou são exportados periodicamente?
- Existe login único (conta Google ou Microsoft) para os funcionários?
- Quem fará a manutenção quando o projeto terminar?

**Níveis de integração**

| Nível | Como funciona | Quando usar |
| --- | --- | --- |
| 0 — Manual | Usuário faz upload e baixa o resultado | MVP e piloto |
| 1 — Arquivo | Leitura automática de planilha ou pasta compartilhada | Dados exportados periodicamente |
| 2 — API | Conexão direta com ERP ou CRM | Uso diário em volume |
| 3 — Automação | O sistema dispara a IA e recebe o resultado (webhook) | Processo maduro e estável |

Para PMEs, comece no nível 0 ou 1 no MVP. Integração com ERP é onde prazo e custo costumam estourar.

**Sinais de alerta**

- Sistema antigo, sem API nem exportação.
- Ninguém na empresa tem senha de administrador.
- O fornecedor do ERP cobra caro ou demora para liberar a integração.
- Não há ninguém para manter a solução depois da entrega.

**Saída do bloco**

Diagrama simples dos sistemas e do fluxo de dados, nível de integração do MVP e lista de acessos que o cliente precisa liberar.

## Bloco 9 — Restrições do projeto

O objetivo é fechar orçamento, prazo e pessoas, e verificar se o retorno justifica o investimento.

**Obrigatórias**

1. Quanto a empresa pode investir para desenvolver a solução?
2. Existe uma data limite? O que acontece se ela não for cumprida?
3. Quem será o ponto focal da empresa, e quantas horas por semana pode dedicar?
4. Quem vai validar as entregas e aprovar cada etapa?
5. Depois da entrega, vocês querem suporte e manutenção contínuos?

**Aprofundamento**

- O investimento pode ser dividido em fases?
- O prazo vem de uma necessidade real (obra, safra, licitação) ou é desejo?
- O código e o modelo treinado ficam com a empresa ou com o desenvolvedor?
- Há outros projetos concorrendo pela atenção da equipe?

**Payback** (cruza os blocos 1 e 6)

```
Payback (meses) = Investimento inicial / (Economia mensal da dor - Custo mensal de operação)
```

Exemplo: investimento de R$ 15.000, economia de R$ 4.000/mês e operação de R$ 500/mês.

1. Ganho líquido mensal: R$ 4.000 − R$ 500 = R$ 3.500
2. Payback: R$ 15.000 ÷ R$ 3.500 ≈ 4,3 meses

Para PMEs, payback acima de 12 meses é difícil de aprovar. Nesse caso, reduza o escopo do MVP em vez de baixar o preço.

**Escopo × prazo × custo:** se o cliente fixa dois, o terceiro se ajusta. Prazo curto com orçamento baixo significa MVP menor.

**Quando o cliente pergunta o preço cedo:** ancore primeiro no custo da dor. Ex.: "30 horas economizadas por mês valem R$ 3.000, fora o risco de processo; um projeto de R$ 20 mil em fases se paga em menos de 8 meses". Só depois apresente valores, e confirme as hipóteses usadas (como o custo da hora).

**Sinais de alerta**

- Orçamento indefinido ("quanto custa?" sem nenhuma referência).
- Ninguém do cliente com tempo para validar as entregas.
- Prazo fixo e escopo crescente.
- Expectativa de manutenção gratuita após a entrega.

**Saída do bloco**

Orçamento e prazo acordados, ponto focal definido, cálculo de payback e modelo de suporte pós-entrega.

## Encerramento da sessão

Os últimos 5 a 10 minutos fecham a sessão com compromissos claros.

1. **Resumo:** a frase-problema validada no bloco 1.
2. **Recomendação preliminar:** seguir, seguir com fase 0 ou não seguir agora, com o motivo em uma frase.
3. **Próximos passos:** o que o cliente envia (amostra de dados, acessos) e o que você entrega.
4. **Participantes:** quem precisa estar na próxima reunião (ex.: o especialista técnico ausente).
5. **Prazo:** data de entrega do Relatório de Descoberta, em até 48 h.

## Bloco 10 — Relatório de Descoberta

O relatório consolida as saídas dos blocos 1 a 9, é entregue ao cliente em até 48 h e serve de base para a proposta comercial.

**Estrutura do relatório**

1. Resumo executivo (meia página, lido em 2 minutos)
2. Frase-problema e custo da dor (bloco 1)
3. Fluxos as-is e to-be (bloco 2)
4. Tipo de solução e justificativa (bloco 3)
5. Inventário e score de prontidão de dados (bloco 4)
6. Indicadores, metas e critério de aceite (bloco 5)
7. Requisitos não funcionais e custo de operação (bloco 6)
8. Matriz de riscos e mitigações (bloco 7)
9. Mapa de integrações e acessos necessários (bloco 8)
10. Escopo do MVP: o que entra e o que não entra
11. Orçamento, prazo e payback (bloco 9)
12. Recomendação e próximos passos

**Score final de viabilidade** (0 a 3 por critério, máximo 18)

| Critério | Bloco de origem |
| --- | --- |
| Dor clara e relevante | 1 |
| IA é o caminho certo | 3 |
| Prontidão dos dados | 4 |
| Retorno viável (payback) | 6 e 9 |
| Riscos controláveis | 7 |
| Comprometimento do cliente | 9 |

**Recomendação**

- **14 a 18 — Seguir:** proposta para o MVP.
- **9 a 13 — Seguir com fase 0:** estruturar dados ou processo antes de desenvolver.
- **Abaixo de 9 — Não seguir agora:** explicar o motivo e indicar o que precisa mudar.

Recomendar "não seguir" quando for o caso constrói reputação: esse cliente tende a voltar quando estiver pronto.

A fase 0 é um produto vendável, não um pré-projeto gratuito. Padronizar a captura de dados, registrar casos e documentar critérios já gera ganho ao cliente e cria a base para o MVP. Ela deve ter escopo, prazo e preço próprios na proposta.

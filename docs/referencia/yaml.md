# Arquivos YAML

A app tem três arquivos de configuração, todos em `config/`. Cada um é validado com
Pydantic **quando a app liga**: se um arquivo tiver erro, a app não sobe e a janela mostra
a lista de problemas em português, com o caminho do campo. É de propósito. Assim o erro
aparece antes da reunião, e não no meio dela.

| Arquivo | O que define | Validado por |
| --- | --- | --- |
| `config/questionario_v1.yaml` | Blocos, perguntas, sinais, scores, revisão e seções do relatório | `src/descoberta/questionario/modelos.py` |
| `config/proposta_v1.yaml` | Padrão da Proposta Comercial e Condições Gerais | `src/descoberta/proposta/modelos.py` |
| `config/llm.yaml` | Provedor e parâmetros do LLM (opcional) | `src/descoberta/llm/configuracao.py` |

**Regras que valem para os três:**

- **Campo desconhecido é erro.** Um erro de digitação (`texo` no lugar de `texto`) não é
  ignorado em silêncio.
- **Textos não podem ficar vazios.** Os espaços nas pontas são removidos.
- **Ids** (`id`, ids de faixa, de critério, de tipo de solução…) só aceitam letras
  minúsculas sem acento, números, `_` e `.`. Exemplos: `b1.o3`, `fase_0`.
- **O número no nome do arquivo é a versão** (`questionario_v2.yaml`), e precisa ser igual
  ao campo `versao` de dentro dele. Arquivos fora desse padrão de nome são ignorados.
- O arquivo é lido com `yaml.safe_load`, que só monta textos, números, listas e
  dicionários e nunca executa código vindo do arquivo.

Para mudar esses arquivos com segurança, veja os guias
[Adaptar o questionário](../guias/adaptar-questionario.md) e
[Adaptar as cláusulas da proposta](../guias/adaptar-clausulas.md).

## Questionário

`config/questionario_v{n}.yaml`. A app carrega todas as versões da pasta. **Sessões novas
usam a versão mais recente**, e cada sessão guarda o número da versão com que foi aberta e
continua usando essa versão para sempre.

### Raiz

| Campo | Tipo | Obrigatório | O que é |
| --- | --- | --- | --- |
| `versao` | inteiro ≥ 1 | sim | Igual ao número do nome do arquivo. |
| `titulo` | texto | sim | Aparece no topo da tela da sessão. |
| `orientacoes` | lista de textos | não | Orientações gerais para conduzir a sessão. |
| `duracao` | objeto | sim | Duração-alvo da sessão (cronômetro). |
| `tipos_solucao` | lista | sim (≥ 1) | Opções do "Tipo de solução" no bloco 3. |
| `blocos` | lista | sim (≥ 1) | Os blocos da sessão, numerados 1, 2, 3… sem pular. |
| `encerramento` | objeto | sim | A aba de encerramento. |
| `revisao` | objeto | sim | O que a revisão pós-sessão pede. |
| `scores` | objeto | sim | Score de prontidão de dados e score final. |

### `duracao`

| Campo | Tipo | O que é |
| --- | --- | --- |
| `aviso_minutos` | inteiro ≥ 1 | Minuto em que o cronômetro muda para a cor de atenção. |
| `limite_minutos` | inteiro ≥ 1 | Minuto em que muda para a cor de limite. Precisa ser maior que o aviso. |

### `tipos_solucao[]`

| Campo | Tipo | O que é |
| --- | --- | --- |
| `id` | id | Gravado na sessão; usado nas condições das perguntas. |
| `rotulo` | texto | Nome da opção na tela ("Visão computacional"). |
| `situacao` | texto | Situação que indica esse tipo, na tabela de apoio do bloco 3. |

### `blocos[]`

| Campo | Tipo | Obrigatório | O que é |
| --- | --- | --- | --- |
| `numero` | inteiro ≥ 1 | sim | Posição do bloco; a sequência começa em 1. |
| `id` | id | sim | Identificador do bloco. |
| `titulo` | texto | sim | Nome da aba. |
| `objetivo` | texto | sim | Mostrado no topo do bloco. |
| `saida_esperada` | texto | sim | O que precisa estar registrado antes de passar ao próximo bloco. |
| `perguntas` | lista | não | Perguntas do bloco (abaixo). |
| `sinais` | lista | não | Sinais de alerta do bloco, cada um com `id` e `texto`. |
| `notas` | lista de textos | não | Notas para o consultor, no fim do bloco. |
| `referencias` | lista | não | Tabelas de consulta (abaixo). |
| `secoes_relatorio` | lista | não | Seções do Relatório de Descoberta (abaixo). Na v1, ficam no bloco 10. |

**`perguntas[]`**

| Campo | Tipo | O que é |
| --- | --- | --- |
| `id` | id | Gravado com a resposta. **Nunca renomeie um id já usado**: as respostas antigas ficariam órfãs. |
| `tipo` | `obrigatoria` ou `aprofundamento` | Obrigatórias aparecem em destaque e contam como pendência; as de aprofundamento ficam recolhidas. |
| `texto` | texto | A pergunta. |
| `condicao` | objeto | Opcional. Com `tipos_solucao: [...]`, a pergunta só aparece se o tipo escolhido no bloco 3 estiver na lista. |

Regras das condições: só valem em blocos **depois do 3** (é o bloco 3 que define o tipo
de solução), e cada tipo citado precisa existir em `tipos_solucao`. Uma pergunta escondida
pela condição não conta como pendência nem entra no relatório.

**`referencias[]`** (tabelas de consulta mostradas no bloco)

| Campo | Tipo | O que é |
| --- | --- | --- |
| `titulo` | texto | Título da tabela; é por ele que uma seção do relatório ou o critério de aceite da proposta cita a tabela. |
| `colunas` | lista de textos | Cabeçalho. |
| `linhas` | lista de listas de textos | Cada linha precisa ter o mesmo número de células que `colunas`. |

**`secoes_relatorio[]`**

| Campo | Tipo | O que é |
| --- | --- | --- |
| `id` | id | Liga a seção ao código que a monta. Na v1: `rel.resumo`, `rel.problema`, `rel.fluxos`, `rel.solucao`, `rel.dados`, `rel.indicadores`, `rel.operacao`, `rel.riscos`, `rel.integracoes`, `rel.escopo`, `rel.orcamento` e `rel.recomendacao`. |
| `titulo` | texto | Título da seção. Um parêntese no fim, como "(bloco 4)", é nota para o consultor e sai do documento do cliente. |
| `blocos` | lista de números | Blocos cujas respostas obrigatórias entram na seção. |
| `respostas` | lista de ids | Outras perguntas ou itens do encerramento que entram na seção. |
| `tabelas` | lista de textos | Títulos de tabelas de `referencias` dos blocos citados em `blocos`. |

!!! warning "Seções novas pedem código"
    O conteúdo próprio de cada seção (por exemplo, a matriz de riscos em `rel.riscos`) é
    montado em `src/descoberta/relatorio/montagem.py`. Um `id` que não esteja nessa lista
    passa na validação do YAML, mas o relatório recusa com "o relatório não sabe montar a
    seção". Dá para mudar títulos, ordem, `blocos`, `respostas` e `tabelas` sem tocar no
    código.

### `encerramento`

| Campo | Tipo | O que é |
| --- | --- | --- |
| `objetivo` | texto | Mostrado no topo da aba. |
| `itens` | lista (≥ 1) | Cada item tem `id`, `titulo` e `descricao`. A resposta é gravada como as das perguntas (com o id do item, ex.: `enc.resumo`) e entra no resumo "Para ler ao cliente". |

### `revisao`

| Campo | Tipo | O que é |
| --- | --- | --- |
| `categorias_risco` | lista (≥ 1) | Opções de categoria da matriz de riscos, cada uma com `id` e `rotulo`. |
| `textos` | lista (≥ 1) | Textos narrativos do relatório que o consultor escreve na revisão (abaixo). |

**`textos[]`**

| Campo | Tipo | O que é |
| --- | --- | --- |
| `id` | id | Gravado com o texto. Os prompts do LLM usam o mesmo id para o limite de palavras. |
| `titulo` | texto | Nome da caixa na revisão. |
| `orientacao` | texto | O que escrever (aparece abaixo do título e vai para o LLM). |
| `apoio` | lista de ids | Perguntas ou itens do encerramento cujas respostas aparecem ao lado, em "O que foi dito na sessão". |

### `scores`

Tem dois scores: `prontidao_dados` (score de dados) e `viabilidade_final` (score final).
Os dois têm:

| Campo | Tipo | O que é |
| --- | --- | --- |
| `bloco` | número | Bloco onde as notas são dadas durante a sessão (precisa existir). |
| `criterios` | lista (≥ 1) | Cada critério recebe uma nota de 0 a 3. O máximo do score é 3 × o número de critérios. |
| `faixas` | lista (≥ 1) | Resultado de cada intervalo de pontuação (abaixo). |

**`faixas[]`**: `id`, `rotulo`, `descricao` (opcional), `min` e `max`. Os intervalos são
fechados (`min` e `max` entram) e precisam cobrir a escala inteira, de 0 ao máximo, sem
buracos nem sobreposição. Os ids de faixa não podem se repetir.

**Critérios do score de dados** (`prontidao_dados.criterios[]`): `id`, `rotulo`,
`ancora_0` e `ancora_3` (o que significa a nota 0 e a nota 3, mostrado ao lado da nota).

**Critérios do score final** (`viabilidade_final.criterios[]`): `id`, `rotulo` e
`blocos_origem` (de que blocos vem a informação, mostrado ao lado da nota; os blocos
precisam existir).

**Ligação entre os dois scores** (só em `prontidao_dados`):

| Campo | O que é |
| --- | --- |
| `criterio_final` | Id do critério do score final cuja nota **não** é dada à mão: ela sai do score de dados. Precisa ser um critério de `viabilidade_final`. |
| `conversao_para_nota` | Lista de `min`, `max` e `nota` (0 a 3): em que nota cada faixa do score de dados se transforma. Cobre de 0 ao máximo sem buracos, e a nota nunca diminui quando o score sobe. |

Os valores da v1 estão em [Fórmulas, scores e faixas](formulas-e-scores.md).

### Ids únicos

Todos os ids de um questionário são únicos **entre si**, de qualquer tipo: tipos de
solução, blocos, perguntas, sinais, seções do relatório, itens do encerramento, critérios,
categorias de risco e textos da revisão. Além disso, cada referência precisa existir: o
`apoio` e as `respostas` citam perguntas ou itens do encerramento existentes; as `tabelas`
de uma seção estão nos blocos dela.

## Modelo da proposta

`config/proposta_v{n}.yaml`. **Propostas novas usam a versão mais recente**, e cada
proposta guarda a versão com que foi criada. Todo modelo é conferido com **todos** os
questionários da pasta, porque uma proposta pode sair de uma sessão de qualquer versão.

### Raiz

| Campo | Tipo | Obrigatório | O que é |
| --- | --- | --- | --- |
| `versao` | inteiro ≥ 1 | sim | Igual ao número do nome do arquivo. |
| `titulo` | texto | sim | Título do documento ("Proposta Comercial"). |
| `aviso` | texto | sim | Aviso de que o modelo é ponto de partida e deve passar por um advogado. Aparece **só para o consultor**, na tela, e não vai ao documento do cliente. |
| `alerta_score_final` | lista de ids de faixa | não | Faixas do score final em que a app avisa antes de criar a proposta (na v1: `nao_seguir`). |
| `criterio_de_aceite` | objeto | não | Textos da seção "Critério de aceite" (abaixo). |
| `padrao` | objeto | sim | O que a app preenche ao criar uma proposta (abaixo). |
| `clausulas` | lista (≥ 1) | sim | As Condições Gerais (abaixo). Ids sem repetição. |

### `criterio_de_aceite`

| Campo | O que é |
| --- | --- |
| `bloco` | Bloco do questionário onde está a tabela de referência. |
| `tabela` | Título de uma tabela de `referencias` desse bloco (na v1: "Critério de aceite em três fases"). |
| `aceite` | O que faz cada fase ser aceita. Vem antes das metas técnicas (indicadores da camada técnica da revisão). |
| `metas_de_negocio` | Explica que as metas de negócio (indicadores da camada de negócio) são acompanhadas, mas não condicionam aceite nem pagamento. |

### `padrao`

| Campo | Tipo | O que é |
| --- | --- | --- |
| `validade_dias` | inteiro ≥ 1 | Validade da proposta. |
| `condicoes_pagamento` | texto | Texto inicial do campo "Condições de pagamento". |
| `impostos` | texto | Texto inicial do campo "Impostos". |
| `reajuste` | texto | Texto inicial do campo "Reajuste". |
| `fases` | lista (≥ 1) | Fases sugeridas (abaixo). |
| `premissas` | lista de textos | Premissas iniciais. As hipóteses marcadas na revisão entram depois delas. |
| `responsabilidades` | lista de textos | Responsabilidades iniciais do cliente. Os próximos passos do cliente, da revisão, entram depois delas. |
| `passos_como_responsabilidade` | dicionário | Substantivo → verbo. Um próximo passo do cliente que começa com o substantivo ganha o verbo ao virar responsabilidade: "Reunião com o Marcos…" vira "Participar da reunião com o Marcos…". Passos que já começam com um verbo ficam como estão. |

**`fases[]`**

| Campo | Tipo | O que é |
| --- | --- | --- |
| `nome` | texto | Nome da fase. |
| `objetivo` | texto | Objetivo da fase. |
| `duracao_semanas` | inteiro ≥ 1 | Duração. |
| `escopo` | lista de textos | Itens de escopo fixos da fase. |
| `entregaveis` | lista de textos | Entregáveis da fase. |
| `escopo_da_revisao` | sim/não | A fase recebe os itens "Entra no MVP" da revisão. **Só uma fase** pode ter `true`. |
| `investimento_da_sessao` | sim/não | A fase recebe o investimento informado no bloco 9. **Só uma fase** pode ter `true`. |
| `faixas_score_final` | lista de ids de faixa | A fase só entra se o score final da sessão estiver numa destas faixas. Vazia: entra sempre. Com o score final incompleto, todas as fases entram, e você tira as que não servirem. |

As faixas citadas em `alerta_score_final` e em `faixas_score_final` precisam existir no
score final de todos os questionários.

### `clausulas[]` (Condições Gerais)

| Campo | Tipo | O que é |
| --- | --- | --- |
| `id` | id | Gravado com os ajustes de cada proposta. Não renomeie um id já usado. |
| `titulo` | texto | Título da cláusula. |
| `texto` | texto | Texto da cláusula. Pode usar os marcadores abaixo, e só eles. |
| `removivel` | sim/não (padrão: não) | Se o consultor pode excluir a cláusula de uma proposta. |

**Marcadores aceitos nos textos das cláusulas** (a montagem troca pelo valor; sem valor,
o documento mostra "A preencher"):

| Marcador | Vira |
| --- | --- |
| `{cliente.empresa}` | a empresa do cliente |
| `{consultor.empresa}` | a empresa do consultor (perfil) |
| `{consultor.nome}` | o nome do consultor (perfil) |
| `{foro}` | a cidade/UF do consultor (perfil) |

Qualquer outro `{…}` no texto é erro, tanto no YAML quanto ao ajustar a cláusula na tela.

## Configuração do LLM

`config/llm.yaml` é **opcional**: sem o arquivo, vale tudo no padrão, e o LLM fica
desligado. A variável de ambiente `DESCOBERTA_LLM_PROVEDOR`, se preenchida, vale mais que o
campo `provedor` do arquivo. **A chave da API nunca fica neste arquivo**: só na variável
`ANTHROPIC_API_KEY` (veja [Variáveis de ambiente e comandos](ambiente-e-comandos.md)).

| Campo | Tipo | Padrão | O que é |
| --- | --- | --- | --- |
| `provedor` | `desligado`, `claude` ou `ollama` | `desligado` | Quem redige os rascunhos. |
| `claude` | objeto | | Parâmetros da API da Anthropic (abaixo). |
| `ollama` | objeto | | Parâmetros do modelo local (abaixo). |

**`claude`**

| Campo | Tipo | Padrão | O que é |
| --- | --- | --- | --- |
| `modelo` | texto | `claude-opus-5-5` | Modelo da API. |
| `esforco` | `low`, `medium`, `high`, `xhigh` ou `max` | `medium` | Quanto o modelo "pensa" antes de responder. |
| `max_tokens` | inteiro de 256 a 64000 | 16000 | Teto do tamanho da resposta. |
| `tempo_limite_s` | número > 0 | 60 | Segundos de espera por resposta. |
| `tentativas` | inteiro de 0 a 5 | 2 | Novas tentativas automáticas em falha de rede ou sobrecarga. |

**`ollama`**

| Campo | Tipo | Padrão | O que é |
| --- | --- | --- | --- |
| `url` | texto | `http://localhost:11434` | Endereço do Ollama. **Precisa ser desta máquina** (`localhost` ou `127.0.0.1`): um Ollama em outro computador deixaria de ser local, e a app recusa. |
| `modelo` | texto | `llama3.1:8b` | Modelo baixado no Ollama. |
| `tempo_limite_s` | número > 0 | 180 | Segundos de espera (modelos locais são mais lentos). |

### Prompts

Os textos enviados ao LLM ficam em `prompts/<id>_v<n>.md`: um cabeçalho YAML entre
`---` e o corpo com `# Sistema` e `# Pedido`. A app usa a **versão mais recente** de cada
id (hoje, `rascunho_revisao_v2` e `rascunho_proposta_v2`), e cada rascunho guarda o rótulo
do prompt usado. Para mudar um prompt, crie a versão seguinte em vez de editar uma já
usada. Detalhes em [Configurar o LLM](../guias/configurar-llm.md#prompts-versionados).

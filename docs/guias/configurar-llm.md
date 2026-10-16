# Configurar o LLM

Depois da sessão, um modelo de linguagem (LLM) pode **sugerir rascunhos** dos textos
narrativos: os seis textos da revisão, o contexto da proposta e o objetivo de cada fase.
Você revisa e aceita ou descarta. É opcional: a app funciona inteira sem ele, e o
relatório e a proposta saem por template.

O LLM **nunca** é usado durante a sessão ao vivo (com o cronômetro rodando, a app recusa),
nem para cálculos, condicionais ou recomendações. Os números vão prontos para o pedido.

Há duas opções:

| | API da Anthropic (`claude`) | Modelo local (`ollama`) |
| --- | --- | --- |
| Onde roda | Nos servidores da Anthropic, pela internet | No seu computador |
| O que sai do computador | O pedido **anonimizado** | Nada |
| Qualidade do texto | Alta | Depende do modelo e do computador |
| Custo | Por uso, na sua conta da Anthropic | Grátis, mas pede um computador com memória (8 GB livres ou mais) |
| Precisa de | Chave da API e internet | Ollama instalado e o modelo baixado |

## 1. Crie o arquivo `.env`

Na pasta da app, copie o arquivo `.env.example` para `.env`. É nele que ficam a escolha do
provedor e a chave, e o `.env` nunca vai para o Git.

!!! warning "Nome exato: `.env`"
    Com as extensões de arquivo ocultas no Windows, o Bloco de Notas salva `.env.txt`, que
    não é lido. O `iniciar.bat` avisa se encontrar um `.env.txt`. No Bloco de Notas, em
    "Salvar como", escolha "Todos os arquivos" e digite `.env`.

## 2a. API da Anthropic

1. Crie uma chave da API no console da Anthropic
   ([console.anthropic.com](https://console.anthropic.com)). O uso é cobrado na sua conta.
2. No `.env`:

    ```ini
    DESCOBERTA_LLM_PROVEDOR=claude
    ANTHROPIC_API_KEY=sua-chave-aqui
    ```

3. Feche a app e abra de novo pelo `iniciar.bat`. A janela preta mostra "Configuracoes
   lidas do arquivo .env".

O modelo padrão é o `claude-opus-5-5`, em `config/llm.yaml`, que também define o esforço,
o teto da resposta, o tempo de espera e as novas tentativas automáticas (veja a
[referência](../referencia/yaml.md#configuracao-do-llm)).

**A chave fica só na variável de ambiente.** Nunca a coloque no `config/llm.yaml`, no
código ou no Git. A app a exibe como `**********` em qualquer log ou mensagem.

## 2b. Modelo local (Ollama)

1. Instale o [Ollama](https://ollama.com) e abra-o.
2. Baixe o modelo (uma vez, com internet):

    ```powershell
    ollama pull llama3.1:8b
    ```

3. No `.env`:

    ```ini
    DESCOBERTA_LLM_PROVEDOR=ollama
    ```

4. Feche a app e abra de novo.

O endereço padrão é `http://localhost:11434`. A app só aceita um Ollama **nesta máquina**
(`localhost` ou `127.0.0.1`) e ignora proxies do sistema: um Ollama em outro computador
deixaria de ser local. Para usar outro modelo, baixe-o com `ollama pull` e mude
`ollama.modelo` no `config/llm.yaml`. Modelos locais são mais lentos: o tempo de espera
padrão é de 180 segundos.

## 3. Confira

Abra a revisão pós-sessão de uma sessão com o cronômetro pausado. O painel **Rascunhos por
LLM** mostra "Provedor: **claude · claude-opus-5-5**" (ou `ollama · llama3.1:8b`). Se
algo faltar, ele diz o quê:

| Mensagem | O que fazer |
| --- | --- |
| Os rascunhos por LLM estão desligados… | Defina `DESCOBERTA_LLM_PROVEDOR` no `.env` e reabra a app. |
| Falta a chave da API… | Defina `ANTHROPIC_API_KEY` no `.env` e reabra a app. |
| A chave da API foi recusada… | Confira a chave (sem espaços ou aspas a mais). |
| Não foi possível falar com a API: sem conexão… | Sem internet: continue com o seu texto e o relatório por template. |
| A API atingiu o limite de uso… / está fora do ar… | Espere um pouco e tente de novo. |
| O Ollama não está rodando nesta máquina… | Abra o Ollama (ou rode `ollama serve`). |
| O modelo '…' não está instalado no Ollama… | Rode o `ollama pull` indicado na mensagem. |
| O modelo recusou este pedido… | Escreva o texto à mão. A app não reenvia para outro modelo. |

Em qualquer falha, o seu texto continua como está, e nada é gravado.

Para **desligar**, use `DESCOBERTA_LLM_PROVEDOR=desligado` (ou deixe em branco, com o
`config/llm.yaml` em `desligado`) e reabra a app.

## Como usar

O passo a passo (pessoas citadas, prévia obrigatória, gerar, aceitar ou descartar) está em
[Revisão pós-sessão](revisao-pos-sessao.md#rascunhos-por-llm). Na proposta é igual, no
mesmo painel.

Alertas que podem vir com um rascunho:

- **marcadores que não estavam no pedido:** o modelo inventou um `[PESSOA_3]`, por exemplo.
  Confira o trecho;
- **resposta cortada no limite de tamanho:** confira o fim do texto;
- **tamanho fora do pedido:** cada texto tem uma faixa de palavras (o resumo executivo,
  por exemplo, vai de 150 a 250). Fora dela, o rascunho chega com o aviso, sem ser cortado.

## Prompts versionados

O que a app pede ao LLM está em arquivos Markdown na pasta `prompts/`, e não no código:

| Arquivo | Para |
| --- | --- |
| `prompts/rascunho_revisao_v2.md` | os textos da revisão (seções do relatório) |
| `prompts/rascunho_proposta_v2.md` | o contexto da proposta e o objetivo das fases |

As versões 1 ficam na pasta como histórico. A app usa a
**versão mais recente** de cada id, e cada rascunho guarda o rótulo usado
(`rascunho_revisao_v2`), junto com o provedor e o modelo.

Cada arquivo tem um cabeçalho YAML e duas partes:

```markdown
---
id: rascunho_revisao
versao: 2
descricao: ...
campos: [titulo, orientacao, limite, texto_atual, contexto]
limites_palavras:
  resumo_executivo: [150, 250]
---

# Sistema
(as instruções fixas)

# Pedido
(a mensagem, com os {{campos}} que a app preenche)
```

**Para mudar um prompt, crie a versão seguinte** (`rascunho_revisao_v3.md`, com
`versao: 3`), em vez de editar uma já usada. A app confere o arquivo ao ligar: o nome
precisa bater com `id` e `versao`, os `{{campos}}` do `# Pedido` precisam ser exatamente
os declarados em `campos`, e o `# Sistema` não pode ter campos. Os ids de `limites_palavras` são os de `revisao.textos` do questionário.

# Adaptar o questionário

O questionário não está no código: ele vem de `config/questionario_v1.yaml`. Dá para mudar
perguntas, sinais de alerta, tabelas de apoio, critérios, faixas e textos da revisão sem
programar. A referência completa dos campos está em
[Arquivos YAML](../referencia/yaml.md#questionario).

## A regra de ouro: crie uma versão nova

Cada sessão guarda a **versão** do questionário com que foi aberta e usa sempre essa
versão. As respostas, os sinais e as notas são gravados pelo **id** que está no YAML
(`b1.o3`, `b4.s2`, `volume`). Por isso:

- **Para mudar o sentido de algo**, como reescrever uma pergunta, trocar faixas ou incluir
  um critério, crie `questionario_v2.yaml`, e não edite a v1. As sessões antigas continuam
  com a v1, como foram feitas, e as sessões novas passam a usar a v2.
- **Nunca renomeie um id** que já foi usado: as respostas antigas ficariam órfãs.
- **Não apague a v1** enquanto houver sessões com ela: a app precisa do arquivo para
  abri-las.
- Corrigir um erro de digitação num texto da versão atual pode ser feito na própria
  versão, desde que o sentido não mude.

## Passo a passo

1. **Faça um backup** do banco ([como](backup-e-restauracao.md)).
2. **Copie** `config/questionario_v1.yaml` para `config/questionario_v2.yaml`, na mesma
   pasta.
3. **Mude a versão** dentro do arquivo novo: `versao: 2`. O número precisa ser igual ao do
   nome do arquivo.
4. **Edite** o que quiser. Use um editor que mostre os espaços, como o VS Code ou o
   Notepad++: no YAML, o recuo (espaços, nunca Tab) faz parte da estrutura.
5. **Confira o arquivo** sem abrir a app:

    ```powershell
    uv run --no-dev python -c "from descoberta.questionario import carregar_questionario as c; c('config/questionario_v2.yaml'); print('ok')"
    ```

6. **Abra a app de novo.** Ela carrega todas as versões ao ligar. Se houver erro, ela
   **não sobe** e a janela preta mostra o problema. Isso é de propósito, para o erro aparecer
   antes da reunião e não no meio dela.
7. **Abra uma sessão nova** e confira: o topo da sessão mostra "versão 2".

## Exemplos

**Incluir uma pergunta obrigatória** no bloco 1. Escolha um id que ainda não exista no
arquivo:

```yaml
      - id: b1.o8
        tipo: obrigatoria
        texto: Quanto tempo a equipe leva para treinar uma pessoa nova nessa tarefa?
```

**Pergunta que só aparece para um tipo de solução** (só nos blocos 4 em diante):

```yaml
      - id: b4.vc9
        tipo: aprofundamento
        texto: As fotos têm sempre a mesma distância e luz?
        condicao:
          tipos_solucao: [visao_computacional]
```

**Um sinal de alerta novo:**

```yaml
    sinais:
      - id: b2.s6
        texto: O processo muda de pessoa para pessoa e não há um jeito "certo".
```

**Mudar a duração-alvo** (o cronômetro muda de cor nesses minutos):

```yaml
duracao:
  aviso_minutos: 60
  limite_minutos: 75
```

## Quando a validação recusa

A mensagem diz o arquivo e o caminho até o campo com problema. Por exemplo, para um
`texo` digitado no lugar de `texto`:

```text
Questionário inválido (questionario_v2.yaml):
  - blocos[id=problema].perguntas[id=b1.o1].texto: campo obrigatório ausente
  - blocos[id=problema].perguntas[id=b1.o1].texo: campo desconhecido (verifique a grafia)
```

Erros comuns:

| Mensagem | O que fazer |
| --- | --- |
| `id duplicado 'b1.o8'` | Os ids são únicos no arquivo inteiro, de qualquer tipo: escolha outro. |
| `o arquivo diz versao 1, mas o nome indica a versão 2` | Mude o `versao:` dentro do arquivo. |
| `perguntas condicionais só podem aparecer depois do bloco 3` | O bloco 3 define o tipo de solução: condicionais só valem do bloco 4 em diante. |
| `lacuna entre as faixas…` ou `…se sobrepõem` | As faixas de um score cobrem de 0 ao máximo sem buracos. Ao incluir um critério, o máximo sobe 3 pontos: refaça as faixas e a conversão do score de dados. |
| `YAML mal formado na linha 120, coluna 7` | Quase sempre é o recuo (um espaço a mais ou a menos) ou um `:` dentro de um texto. Ponha o texto entre aspas. |
| `Modelo da proposta inválido: proposta_v1.yaml × questionario_v2.yaml: …` | O modelo da proposta cita ids de faixa do score final, ou uma tabela do bloco 5, que a v2 não tem. Mantenha esses ids ou crie também uma `proposta_v2.yaml` (veja [Adaptar as cláusulas](adaptar-clausulas.md)). |

## O que o YAML não muda

Algumas coisas estão no código, de propósito, porque dependem de contas ou da montagem dos
documentos:

- **Os campos numéricos** (horas, frequência, custo da hora, operação, economia,
  investimento) e os blocos onde aparecem (1, 6 e 9), em `src/descoberta/campos.py`. As
  fórmulas ficam em `src/descoberta/dominio/`.
- **O bloco do tipo de solução** é o 3.
- **As seções do relatório:** dá para mudar títulos, ordem e o que entra em cada uma
  (`blocos`, `respostas`, `tabelas`), mas o `id` precisa ser um dos 12 que o relatório sabe
  montar (`rel.resumo`, `rel.problema`…).
- **Os limites de palavras dos rascunhos por LLM** ficam nos prompts, pelo id do texto da
  revisão. Se você criar um texto novo em `revisao.textos`, o pedido ao LLM diz só "o que a
  orientação pedir", e o rascunho não ganha o alerta de tamanho, até um prompt novo incluir
  o id (veja
  [Configurar o LLM](configurar-llm.md#prompts-versionados)).

## Licença do conteúdo

O conteúdo do questionário é a metodologia do Modelo de Descoberta, sob **CC BY 4.0**: você
pode adaptar e usar inclusive comercialmente, **dando o crédito** ao autor e indicando que
houve mudanças. Veja [A metodologia](../explicacao/metodologia.md#licenca-cc-by-40).

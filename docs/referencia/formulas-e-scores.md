# Fórmulas, scores e faixas

Todas as contas ficam na camada `dominio` (`src/descoberta/dominio/`), em Python puro e com
testes. A tela e o relatório usam o mesmo cálculo (`dominio/painel.py`), por isso os
números são sempre iguais nos dois lugares. **Nenhuma conta passa pelo LLM**, e nenhum
número é tirado do texto das respostas: cada número tem um campo próprio, em "Números do
bloco".

Os limites dos scores (critérios e faixas) vêm do questionário (YAML), e não do código.
Os valores abaixo são os da **versão 1** (`config/questionario_v1.yaml`).

## Números de entrada

| Campo na tela | Bloco | Nome no banco |
| --- | --- | --- |
| Horas por ocorrência (h) | 1 | `horas_por_ocorrencia` |
| Ocorrências | 1 | `frequencia_quantidade` |
| Período da frequência (por dia útil, por semana, por mês) | 1 | `frequencia_periodo` |
| Custo da hora (R$) | 1 | `custo_hora` |
| Chamadas por dia | 6 | `chamadas_por_dia` |
| Custo por chamada (R$) | 6 | `custo_por_chamada` |
| Custo fixo mensal (R$) | 6 | `custo_fixo_mes` |
| Horas economizadas por mês (h) | 9 | `horas_economizadas_mes` |
| Outros ganhos mensais (R$) | 9 | `outros_ganhos_mes` |
| Investimento (R$) | 9 | `investimento` |

**Como digitar:** vírgula para decimais e ponto para milhar: `7,5`, `20.000`, `3.000,50`.
Também valem `20000` e `R$ 400`. **`7.5` é recusado**, com o aviso "use vírgula para
decimais": no Brasil o ponto separa milhares, e ler `7.5` como 75 (ou como 7,5) sem avisar
seria pior do que pedir a vírgula. Números negativos não são aceitos.

**Precisão:** dinheiro e horas são guardados e calculados como decimais exatos (`Decimal`),
nunca como número de ponto flutuante. Com ponto flutuante, 0,1 + 0,2 daria
0,30000000000000004. Na tela, os resultados aparecem com uma casa decimal (7,7 meses), e o
dinheiro com duas (R$ 6.000,00).

## Custo da dor (bloco 1)

O custo mensal da dor é o **teto do orçamento razoável**.

```text
ocorrências por mês = ocorrências × fator do período
    por dia útil: × 22      por semana: × 52 / 12      por mês: × 1
horas da dor por mês = horas por ocorrência × ocorrências por mês
custo da dor por mês = horas da dor por mês × custo da hora
```

Um mês tem **22 dias úteis** (`DIAS_UTEIS_POR_MES`). A conta multiplica antes de dividir:
3 por semana × 52 / 12 dá exatamente 13, e não 12,999…

## Custo de operação (bloco 6)

```text
custo de operação por mês = chamadas por dia × custo por chamada × 22 + custo fixo mensal
```

- Só o custo fixo informado: a parte variável conta como zero.
- Só a parte variável: o custo fixo conta como zero, mas é preciso informar **as duas**
  metades (chamadas por dia e custo por chamada).
- Nada informado: o painel mostra o que falta.

## Economia mensal (bloco 9)

```text
economia por mês = horas economizadas por mês × custo da hora + outros ganhos mensais
```

"Outros ganhos mensais" é opcional (vazio conta como zero). O custo da hora é o mesmo do
bloco 1.

## Payback

```text
payback (meses) = investimento / (economia por mês − custo de operação por mês)
```

- Se a economia **não supera** o custo de operação, o projeto nunca se paga. O painel
  mostra "não se paga" em vez de um número.
- **Acima de 12 meses**, o painel avisa: "acima de 12 meses: difícil de aprovar numa PME"
  (`LIMITE_PAYBACK_MESES`, do bloco 9 do Modelo de Descoberta).

## Score de prontidão de dados (bloco 4)

Cinco critérios, cada um com nota de 0 a 3, **máximo 15**. O resultado só aparece quando
os cinco têm nota; antes disso, o painel mostra a soma parcial e o que falta.

| Critério | Nota 0 | Nota 3 |
| --- | --- | --- |
| Disponibilidade | Não existe | Exportável hoje |
| Volume | Dezenas de casos | Milhares de casos |
| Rótulos / resultado | Ausente | Registrado em todos |
| Qualidade | Caótica | Padronizada |
| Acesso legal (LGPD) | Incerto | Base legal clara |

**Faixas:**

| Pontuação | Resultado | O que significa |
| --- | --- | --- |
| 0–5 | Fase 0 | Começar por organizar e coletar dados. |
| 6–10 | MVP com ressalvas | |
| 11–15 | Pronto para modelar | |

**Conversão para o score final.** O critério "Prontidão dos dados" do score final não
recebe nota à mão: ela sai deste score.

| Score de dados | Nota no score final |
| --- | --- |
| 0–2 | 0 |
| 3–5 | 1 |
| 6–10 | 2 |
| 11–15 | 3 |

## Score final de viabilidade (bloco 10)

Seis critérios, cada um com nota de 0 a 3, **máximo 18**. Um deles ("Prontidão dos
dados") vem da conversão acima.

| Critério | Informação de |
| --- | --- |
| Dor clara e relevante | bloco 1 |
| IA é o caminho certo | bloco 3 |
| Prontidão dos dados | bloco 4 (derivada do score de dados) |
| Retorno viável (payback) | blocos 6 e 9 |
| Riscos controláveis | bloco 7 |
| Comprometimento do cliente | bloco 9 |

**Faixas:**

| Pontuação | Recomendação | O que fazer |
| --- | --- | --- |
| 0–8 | Não seguir agora | Explicar o motivo e indicar o que precisa mudar. |
| 9–13 | Seguir com fase 0 | Estruturar dados ou processo antes de desenvolver. |
| 14–18 | Seguir | Proposta para o MVP. |

Na Proposta Comercial, a faixa "Não seguir agora" gera um aviso antes de criar a proposta
(`alerta_score_final` do modelo da proposta), e as fases sugeridas dependem da faixa (veja
[Arquivos YAML](yaml.md#modelo-da-proposta)).

## Matriz de riscos (revisão pós-sessão)

Cada risco tem probabilidade e impacto em três níveis (baixo, médio e alto). A gravidade
da célula soma as posições dos dois eixos (baixo = 0, médio = 1, alto = 2):

| Soma | Gravidade | Exemplos |
| --- | --- | --- |
| 0 ou 1 | baixa | baixo × baixo, baixo × médio |
| 2 | média | médio × médio, alto × baixo |
| 3 ou 4 | alta | alto × médio, alto × alto |

A grade 3×3 é desenhada como no papel: impacto de cima (alto) para baixo e probabilidade da
esquerda (baixa) para a direita. O canto de cima à direita é o mais grave. Um risco com
probabilidade **e** impacto altos sem mitigação aparece como pendência da revisão.

## Caso de referência: Construtora Alvorada (Roberto)

É o caso usado nos testes e no banco de demonstração.

| Entrada | Valor |
| --- | --- |
| Horas por ocorrência | 4 h |
| Ocorrências | 15 por mês |
| Custo da hora | R$ 100 (hipótese) |
| Custo fixo mensal | R$ 400 (hipótese) |
| Horas economizadas por mês | 30 h (hipótese) |
| Investimento | R$ 20.000 |
| Notas do score de dados | 1, 1, 1, 0, 1 |
| Notas do score final (fora a de dados) | 3, 2, 2, 2, 2 |

| Resultado | Conta | Valor |
| --- | --- | --- |
| Horas da dor | 4 × 15 | **60 h/mês** |
| Custo da dor | 60 × R$ 100 | R$ 6.000,00/mês |
| Custo de operação | 0 + R$ 400 | R$ 400,00/mês |
| Economia | 30 × R$ 100 | R$ 3.000,00/mês |
| Payback | 20.000 / (3.000 − 400) | **≈ 7,7 meses** |
| Score de dados | 1 + 1 + 1 + 0 + 1 | **4 de 15** → Fase 0 (nota 1 no score final) |
| Score final | 3 + 2 + 1 + 2 + 2 + 2 | **12 de 18** → **Seguir com fase 0** |

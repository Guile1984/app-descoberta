# Revisão pós-sessão

A revisão é a página onde você prepara, depois da reunião, o que o relatório precisa e
que não sai direto das respostas. Ela fica separada da tela ao vivo. Abra pela sessão, em
**Revisão pós-sessão →**.

Tudo salva sozinho, como na sessão. Os itens de lista são incluídos com o botão
**Incluir** de cada lista.

## O quadro "Falta preencher"

À direita, o quadro **Falta preencher** lista, por seção, o que ainda impede um relatório
completo, com um link para cada parte. Quando está tudo certo, ele mostra "✓ Nada falta
nas saídas da revisão". Ele também avisa quantas obrigatórias ficaram sem resposta na tela
da sessão.

O que conta como pendência:

| Parte | Vira pendência quando… |
| --- | --- |
| Textos do relatório | um texto está em branco |
| Matriz de riscos | não há nenhum risco, ou um risco tem probabilidade **e** impacto altos sem mitigação |
| Indicadores de sucesso | não há nenhum indicador de **negócio**, ou um indicador está sem valor atual, meta, prazo ou como medir |
| Escopo do MVP | não há nenhum item que entra no MVP, ou nenhum que fica de fora |
| Próximos passos | não há nenhum passo, ou um passo está sem prazo |

As pendências não bloqueiam nada: o relatório pode ser gerado a qualquer momento, e os
trechos que faltam saem marcados com "A preencher".

## Passo a passo

### 1. Textos do relatório

Seis textos narrativos (na v1 do questionário): resumo executivo, frase-problema, fluxo
atual (as-is), fluxo futuro (to-be), tipo de solução e justificativa, e recomendação. Cada
caixa mostra a orientação do que escrever e, em **O que foi dito na sessão**, as respostas
que servem de apoio.

Se o LLM estiver ativo, **Sugerir rascunho** pede um texto ao LLM. Veja
[Configurar o LLM](configurar-llm.md) e a seção [Rascunhos por LLM](#rascunhos-por-llm),
abaixo.

### 2. Matriz de riscos

Para cada risco: descrição, categoria (LGPD, viés, explicabilidade, responsabilidade
técnica, segurança, dependência de fornecedor ou outro), probabilidade, impacto e
mitigação. Os riscos ganham números (R1, R2…) e aparecem na **grade 3×3**, desenhada como
no papel: impacto de cima para baixo e probabilidade da esquerda para a direita. O canto
de cima à direita é o mais grave. A regra da gravidade está em
[Fórmulas, scores e faixas](../referencia/formulas-e-scores.md#matriz-de-riscos-revisao-pos-sessao).

### 3. Indicadores de sucesso

Indicador → valor atual → meta → prazo → como medir, nas duas camadas: **negócio** (horas,
prazo, dinheiro) e **técnica** (acerto do modelo, por exemplo). Esses campos são texto
("Recall ≥ 95%") e não entram em cálculos. Na proposta, os técnicos entram no critério de
aceite e os de negócio nas metas acompanhadas.

### 4. Escopo do MVP

Cada item **Entra no MVP** ou **Fica de fora**. Na proposta, os que entram vão para o
escopo da fase do MVP, e os que ficam de fora vão para "Fora do escopo".

### 5. Próximos passos

Ação, responsável (cliente ou consultor) e prazo. Na proposta, os passos do cliente viram
responsabilidades do cliente.

### 6. Hipóteses dos cálculos

A tabela **Hipóteses dos cálculos** lista os números da sessão. Marque os que **você
estimou** e que o cliente ainda precisa confirmar (o custo da hora, por exemplo). Os
valores em si são editados na tela da sessão.

Uma hipótese marcada aparece assim:

- **no relatório:** com `*` nas seções e destacada na memória de cálculo (Anexo B), com a
  nota "Calculado com hipóteses do consultor, a confirmar";
- **na proposta nova:** nas premissas, com "(hipótese do consultor, a confirmar com o
  cliente)".

## Rascunhos por LLM

Opcional, e só com o LLM configurado. No painel **Rascunhos por LLM**, à direita:

1. **Confira as pessoas citadas.** O cliente, a empresa, o consultor e os dados da
   proposta já são trocados por marcadores. Nomes citados de passagem (um funcionário do
   cliente) só são trocados se estiverem na lista. A app sugere os nomes que encontra nas
   respostas e anotações ("Parecem nomes de pessoas"); inclua os que forem pessoas.
2. **Veja a prévia** (**Ver prévia**). É exatamente o texto que sai, com a tabela dos
   marcadores e dos valores reais (essa tabela fica no seu computador). Procure algum nome,
   telefone ou endereço que ainda apareça. Se estiver tudo certo, clique em **Confirmar:
   está anonimizado**. A confirmação vale até a lista de pessoas ou os dados do cliente
   mudarem.
3. **Peça o rascunho** em **Sugerir rascunho**, na caixa do texto. O rascunho aparece ao
   lado, com o provedor, o modelo e a versão do prompt. **Aceitar** substitui o seu texto
   (a app pede confirmação), e **Descartar** o descarta. Nada muda no seu texto sem
   aceitar.

**Usar anotações internas como contexto** vem desligado, como na versão cliente do
relatório. Ligado, as anotações e os sinais de alerta vão no pedido (anonimizados), e o
conteúdo deles pode aparecer no texto, que o cliente vai ler.

Por que é assim: [Privacidade, LGPD e anonimização](../explicacao/privacidade-lgpd.md).

## Depois

Confira o relatório em **Relatório →** e siga o guia
[Gerar e registrar relatório e proposta](relatorio-e-proposta.md).

# Conduzir uma sessão ao vivo

Este guia é para a reunião em si, quando o cliente está falando e você anota sem travar a
conversa. Se é a sua primeira vez com a app, faça antes o
[tutorial](../tutorial/primeira-sessao.md).

## Antes da reunião

1. **Cadastre o cliente:** em **Clientes → Novo cliente**, preencha pelo menos o nome do
   contato e a empresa.
2. **Abra a sessão:** na página do cliente, confira a data e clique em **Abrir nova
   sessão**. A sessão usa a versão mais recente do questionário e guarda essa versão para
   sempre.
3. **Preparação:** no topo da sessão, a caixa **Preparação** (aberta enquanto o status é
   "Preparação") tem o **Contexto prévio**, para o que você já sabe, e **Amostra de dados
   recebida**, para marcar se a amostra chegou.
4. **Teste o teclado:** tecle `Ctrl+/` e confira os atalhos. Eles estão também na
   [referência](../referencia/atalhos.md).

!!! tip "Sem internet, sem problema"
    A sessão inteira funciona sem internet. O LLM nunca é usado durante a sessão ao vivo:
    enquanto o cronômetro roda, a app recusa gerar rascunhos.

## A tela da sessão

- **À esquerda**, as perguntas do bloco aberto, com o objetivo e a saída esperada no topo.
  As **obrigatórias** aparecem em destaque. As de **aprofundamento** ficam recolhidas em
  "Aprofundamento (n)": use quando sobrar tempo ou quando uma resposta ficar vaga.
- **À direita**, os sinais de alerta do bloco, o painel de **Cálculos** e as
  **Anotações**.
- **No topo**, o cronômetro, o total de obrigatórias pendentes, o status da sessão e os
  botões **Revisão pós-sessão →** e **Relatório →**.

## Durante a conversa

**Comece o cronômetro** com `Alt+T` (ou o botão **Iniciar**). A duração-alvo da v1 é de 60
a 90 minutos. O cronômetro muda de cor aos **75 min** (aviso) e de novo aos **90 min**
(limite). Enquanto roda, um ponto pulsa ao lado do tempo. `Alt+T` também pausa e retoma.

**Navegue pelos blocos** com `Alt+1` … `Alt+9` e `Alt+0` (bloco 10), ou clicando nas abas.
Cada aba mostra quantas obrigatórias faltam naquele bloco. A navegação é livre: dá para ir
e voltar quando a conversa pular de assunto.

**Responda.** Cada campo **salva sozinho** quando você para de digitar ou sai dele. Ao lado
do campo, aparece "Salvando…" e depois "Salvo às 14:32".

!!! warning "Se aparecer “Não salvo”"
    "⚠ Não salvo: a app não respondeu" quer dizer que o pedido não chegou à app: a janela
    preta foi fechada, por exemplo. **Copie o texto antes de sair da página** e abra a app
    de novo. "⚠ Não salvo: …" com outro motivo (um número inválido, por exemplo) diz o que
    corrigir.

**Escolha o tipo de solução no bloco 3.** A opção "Tipo de solução" abre as perguntas
**condicionais** dos blocos seguintes. Por exemplo, "Visão computacional" abre perguntas
sobre imagens. Elas aparecem com o selo "condicional". Trocar o tipo esconde as
condicionais de outro tipo, e as respostas delas deixam de contar como pendência e de
entrar no relatório, mas continuam guardadas.

**Registre os números nos campos próprios.** Os blocos 1, 6 e 9 têm a caixa **Números do
bloco** (horas, frequência, custo da hora, operação, economia, investimento). Use vírgula
para decimais (`7,5`) e ponto para milhar (`20.000`). Os números ficam nesses campos, e não
no texto das respostas: a app nunca tira números do texto.

**Dê as notas dos scores.** No bloco 4, as cinco notas do score de prontidão de dados (0 a
3, com o que significam o 0 e o 3). No bloco 10, as notas do score final. A nota
"Prontidão dos dados" do score final não é dada à mão: ela sai do score de dados.

**Acompanhe os cálculos** no painel à direita (`Alt+C`): custo da dor, custo de operação,
economia, payback, os dois scores e os sinais marcados. Eles se atualizam sozinhos a cada
número ou nota salva. Enquanto falta algo, o painel diz o quê ("falta: custo da hora").
Payback acima de 12 meses aparece em destaque. As fórmulas estão em
[Fórmulas, scores e faixas](../referencia/formulas-e-scores.md).

**Marque os sinais de alerta** com um clique, ou com `Alt+S` e depois `Tab` e `Espaço`.
Marcado, o sinal ganha um campo de **Observação**. Os sinais vão só para a versão interna
do relatório.

**Anote o que não cabe numa pergunta:** `Alt+N`, escreva e `Ctrl+Enter`. A anotação fica
ligada ao bloco aberto, e o cursor volta ao campo onde você estava. As anotações também vão
só para a versão interna.

**Ache o que falta:** `Alt+P` leva à próxima obrigatória sem resposta e, quando o bloco está
em dia, ao próximo bloco com pendências. O indicador do topo mostra o total, ou "Todas as
obrigatórias respondidas". `Esc` volta ao último campo de resposta.

## Encerramento

Nos últimos 5 a 10 minutos, `Alt+R` abre o **Encerramento**: resumo, recomendação
preliminar, próximos passos, participantes da próxima reunião e prazo do relatório. Abaixo
deles, **Para ler ao cliente** monta um resumo pronto, com a indicação dos cálculos (faixa
do score final e payback). Se ainda houver obrigatórias pendentes, o resumo avisa antes.

No fim, **pause o cronômetro** (`Alt+T`) e mude o **Status** para "Concluída", se quiser.
O cronômetro pausado também libera os rascunhos por LLM na revisão.

## Depois

Siga para a [revisão pós-sessão](revisao-pos-sessao.md). O que ficou faltando nas
respostas pode ser completado depois, na mesma tela da sessão.

**Excluir:** **Excluir sessão** (na sessão) e **Excluir** (no cliente) apagam tudo o que foi
registrado, inclusive as versões de relatório e de proposta, e não dá para desfazer. Se
houver dúvida, faça um [backup](backup-e-restauracao.md) antes.

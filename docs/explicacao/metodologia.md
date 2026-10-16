# A metodologia: o Modelo de Descoberta

A app é a versão digital de uma metodologia em texto: o **Modelo de Descoberta — Apps de IA
para PMEs**. O texto completo está em
[Modelo de Descoberta (texto completo)](../modelo-descoberta.md). Esta página explica a
ideia por trás dele e como a app a traduz.

## Por que uma sessão de descoberta

Pequenas e médias empresas chegam querendo "usar IA". Antes de qualquer proposta, a sessão
responde **três perguntas**:

1. **A dor é real?** Ela tem nome, tamanho em horas e reais e um dono.
2. **A IA é o caminho certo?** Ou uma automação comum, ou só organizar os dados primeiro,
   resolve melhor e mais barato.
3. **Os dados permitem fazê-la?** Eles existem, são suficientes, têm o resultado registrado
   e podem ser usados legalmente.

Numa PME, quem decide costuma ser o dono, os dados vivem em planilhas, WhatsApp e num ERP
básico, o orçamento é curto e raramente há equipe de TI. O modelo foi feito para esse
cenário: 60 a 90 minutos, com o decisor presente, em linguagem de negócio. A tradução para
requisitos técnicos é trabalho do consultor, depois da sessão.

## Os blocos

| Bloco | Objetivo |
| --- | --- |
| 1. Problema de negócio | Sair com uma dor nomeada, medida e com dono. |
| 2. Processo atual × futuro | Desenhar como a tarefa é feita hoje e onde a IA entraria. |
| 3. Adequação de IA | Decidir se o projeto usa IA e de que tipo. "Não precisa de IA" é uma resposta válida e gera confiança. |
| 4. Dados | Medir quanto falta para os dados serem usáveis. |
| 5. Critérios de sucesso | Transformar "quero que funcione bem" em números combinados antes do desenvolvimento. |
| 6. Requisitos não funcionais | Traduzir o dia a dia do cliente em requisitos técnicos e estimar o custo mensal de operação. |
| 7. Riscos e compliance | Mapear riscos legais, éticos e de segurança e definir mitigações antes do início. |
| 8. Integração e infraestrutura | Definir de onde a IA lê os dados e onde entrega o resultado. |
| 9. Restrições do projeto | Fechar orçamento, prazo e pessoas, e verificar se o retorno justifica o investimento. |
| 10. Relatório de Descoberta | Consolidar tudo num relatório entregue em até 48 h, base da proposta comercial. |

Depois dos blocos vem o **encerramento**: nos últimos 5 a 10 minutos, o resumo, a
recomendação preliminar, os próximos passos, quem precisa estar na próxima reunião e o
prazo do relatório.

## Como a app traduz o modelo

| No modelo | Na app |
| --- | --- |
| Perguntas obrigatórias, feitas em toda sessão | Em destaque, contadas como pendência por bloco e no total (`Alt+P` leva à próxima). |
| Perguntas de aprofundamento, quando o tempo permite | Recolhidas em "Aprofundamento", sem contar como pendência. |
| Saída esperada de cada bloco | Mostrada no topo do bloco. |
| Sinais de alerta, anotados durante a conversa | Botões de um clique (`Alt+S`), com observação. Vão só para a versão interna do relatório. |
| O bloco 3 define o tipo de solução, que abre perguntas específicas | O "Tipo de solução" do bloco 3 mostra ou esconde as perguntas condicionais (na v1, as de visão computacional no bloco 4). |
| Custo da dor, custo de operação e payback | Campos numéricos nos blocos 1, 6 e 9 e cálculo ao vivo no painel. |
| Score de prontidão de dados e score final | Notas de 0 a 3 nos blocos 4 e 10, com a faixa e a recomendação na hora. |
| Relatório de Descoberta em até 48 h | Revisão pós-sessão com o que falta, e relatório por template em PDF, Word e Markdown. |

As regras (critérios, faixas, perguntas, sinais) estão no **YAML do questionário**, e não
no código: a metodologia pode evoluir numa versão nova sem programação (veja
[Adaptar o questionário](../guias/adaptar-questionario.md)). O código só garante as contas
e a consistência.

## As três recomendações

O score final (0 a 18) leva a uma de três recomendações:

- **Seguir (14 a 18):** proposta para o MVP.
- **Seguir com fase 0 (9 a 13):** estruturar dados ou processo antes de desenvolver.
- **Não seguir agora (abaixo de 9):** explicar o motivo e indicar o que precisa mudar.

Duas ideias do modelo aparecem no comportamento da app:

- **Recomendar "não seguir" constrói reputação.** Esse cliente tende a voltar quando
  estiver pronto. Por isso a app avisa antes de criar uma proposta com essa recomendação,
  e só cria com a sua confirmação.
- **A fase 0 é um produto vendável**, e não um pré-projeto gratuito. Padronizar a captura
  de dados, registrar casos e documentar critérios já gera ganho e cria a base para o MVP.
  Por isso o modelo da proposta traz a Fase 0 com escopo, entregáveis, prazo e preço
  próprios, e ela entra sozinha quando o score indica "seguir com fase 0".

O caso de referência, o da Construtora Alvorada, termina assim: dor clara de 60 h/mês, mas
dados ainda desorganizados (score de dados 4 de 15). O score final 12 leva a "seguir com
fase 0". Os números estão em
[Fórmulas, scores e faixas](../referencia/formulas-e-scores.md#caso-de-referencia-construtora-alvorada-roberto).

## Licença: CC BY 4.0

O Modelo de Descoberta (`docs/modelo-descoberta.md`) e o conteúdo do questionário
(`config/questionario_v1.yaml`) são © 2026 Guilherme Ferraz Stauffer, sob a
[Creative Commons Atribuição 4.0 Internacional](https://creativecommons.org/licenses/by/4.0/deed.pt-br).

Você pode copiar, adaptar e usar a metodologia, inclusive comercialmente (nas suas
sessões ou num questionário adaptado), **desde que dê o crédito**, indique o link da
licença e diga se fez alterações. Sugestão de crédito:

> Baseado no "Modelo de Descoberta — Apps de IA para PMEs", de Guilherme Ferraz Stauffer
> (https://github.com/Guile1984/app-descoberta), licenciado sob CC BY 4.0.

**Por que uma licença diferente da do código (MIT):** a metodologia é um texto, e as
licenças Creative Commons foram feitas para textos. A CC BY garante o crédito também nas
adaptações. O texto da licença está em
[`LICENSE-METODOLOGIA.md`](https://github.com/Guile1984/app-descoberta/blob/main/LICENSE-METODOLOGIA.md).

# Gerar e registrar relatório e proposta

Os dois documentos saem dos dados da sessão e da revisão, por template, sem internet e sem
LLM. Eles são **separados**: renegociar a proposta nunca altera o relatório nem as versões
dele.

## Relatório de Descoberta

Abra pela sessão ou pela revisão, em **Relatório →**.

### Conferir a prévia

A página mostra o documento como vai sair. No alto, escolha a versão:

- **Versão cliente:** sem sinais de alerta e sem anotações.
- **Versão interna:** com o **Anexo C** (sinais de alerta marcados, sinais por bloco e
  anotações livres), a faixa "USO INTERNO" na capa e o aviso no rodapé de cada página.
  **Não envie ao cliente.**

Se faltar algo, um aviso diz quantos trechos estão marcados com "A preencher" e onde
completar (na revisão ou na tela da sessão).

O relatório tem capa, as 12 seções do bloco 10 do questionário, o **Anexo A** (respostas da
sessão), o **Anexo B** (memória de cálculo: entradas, contas e scores, com as hipóteses
destacadas) e o **termo de ciência e validação**, para o cliente assinar. Respostas de
perguntas condicionais escondidas pelo tipo de solução não entram. Os números são os
mesmos do painel da sessão.

### Baixar um rascunho

Em **Baixar (rascunho)**: **PDF**, **Word** ou **Markdown**. O arquivo é gerado na hora,
com os dados atuais, e nada é gravado. O rodapé diz "Rascunho não registrado", com a data e
a hora. Use para revisar, ou para mandar a alguém revisar.

### Registrar a versão enviada

Quando for enviar ao cliente, clique em **Registrar versão enviada (cliente)** (ou
"(interna)", na versão interna). A app:

1. gera o PDF com o próximo número de versão (1, 2, 3…; a numeração é uma só para as
   versões cliente e interna da sessão);
2. imprime no rodapé de **cada página** "Versão N (cliente), emitida em dd/mm/aaaa hh:mm ·
   hash" seguido dos 12 primeiros caracteres do hash;
3. guarda o PDF no banco, exatamente como foi emitido.

Em **Versões registradas**, o link **PDF** devolve o arquivo guardado, byte a byte, mesmo que
os dados da sessão mudem depois. Envie **esse** PDF.

!!! info "Conferir uma cópia assinada"
    Compare o número da versão e o hash do rodapé da cópia com a lista de versões
    registradas (passe o mouse sobre o hash para ver os dois hashes completos). O hash do
    rodapé é o SHA-256 do texto do relatório; o do arquivo PDF fica guardado à parte. Por que
    dois: [Modelo de dados](../referencia/modelo-de-dados.md#versao_relatorio).

## Proposta Comercial

Abra pela revisão ou pelo relatório, em **Proposta →**.

### Criar

A primeira vez mostra o que vai entrar na proposta:

- **as fases** do modelo (`config/proposta_v1.yaml`), escolhidas pela faixa do score final:
  "Seguir com fase 0" traz a Fase 0 e o MVP, e "Seguir" traz só o MVP. Com o score final
  incompleto, todas as fases entram, e você tira as que não servirem;
- **o escopo do MVP**, com os itens "Entra no MVP" da revisão, e o **investimento** do
  bloco 9 na fase do MVP;
- **fora do escopo**, com os itens que ficam fora do MVP;
- **premissas** do modelo, mais as hipóteses marcadas na revisão;
- **responsabilidades do cliente**, do modelo, mais os próximos passos do cliente.

Clique em **Criar proposta**. Se o score final indicar **"Não seguir agora"**, a app avisa
antes, e o botão vira **Criar mesmo assim**. A proposta guarda que foi criada depois do
aviso.

A proposta é uma **cópia**: mudar a revisão depois não a altera. Para começar de novo a
partir da revisão atual, use **Recriar a partir da revisão**. As versões já registradas
ficam guardadas.

### Editar

Tudo salva sozinho:

- **Dados do cliente para a proposta:** representante (quem assina), cargo, CPF ou CNPJ
  (conferido pelos dígitos), e-mail, cidade e UF;
- **Contexto da proposta** (o LLM pode sugerir um rascunho);
- **Fases** (nome, objetivo, duração em semanas, investimento), **Escopo por fase**,
  **Entregáveis**, **Fora do escopo**, **Premissas e hipóteses** e **Responsabilidades do
  cliente**. Excluir uma fase exclui junto o escopo e os entregáveis dela;
- **Condições:** pagamento, impostos, reajuste e validade (dias);
- **Condições Gerais:** veja [Adaptar as cláusulas da proposta](adaptar-clausulas.md).

Os avisos no alto apontam itens de escopo repetidos em mais de uma fase e a diferença
entre a soma das fases e o investimento da sessão, que é o usado no payback do relatório.
Eles só alertam e não mudam nada.

!!! warning "Revise com um advogado"
    O modelo da proposta é um ponto de partida, não aconselhamento jurídico. O aviso
    aparece para você na tela, e não vai ao documento do cliente.

### Conferir, baixar e registrar

**Documento da proposta →** mostra a prévia. A proposta tem 11 seções (identificação das
partes, contexto, escopo por fase, entregáveis e cronograma, investimento, condições,
premissas, responsabilidades, critério de aceite, validade e aceite, com as duas
assinaturas na mesma página) e o **Anexo — Condições Gerais**, coberto pela mesma
assinatura e pelo mesmo hash.

- **Baixar (rascunho):** PDF, Word ou Markdown, como no relatório.
- **Registrar versão enviada:** como no relatório, com **numeração própria** e o rodapé
  "Proposta · Versão N…". O texto das Condições Gerais fica **congelado** com a versão:
  ajustar uma cláusula depois não muda o que foi enviado.
- **PDF único:** junta o relatório (a última versão cliente registrada, ou o rascunho
  cliente) e a proposta (a última versão registrada, ou o rascunho). Cada parte mantém o
  próprio rodapé, com versão e hash, e a sua numeração de páginas.

## Arquivos

Os nomes dos arquivos baixados seguem o padrão
`relatorio-descoberta-<empresa>-<data da sessão>-<versão>[-vN].<formato>`. Por exemplo:
`relatorio-descoberta-construtora-alvorada-2026-10-07-cliente-v1.pdf`.

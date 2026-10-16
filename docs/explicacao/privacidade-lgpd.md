# Privacidade, LGPD e anonimização

Numa sessão de descoberta aparecem dados pessoais: o nome do cliente e da equipe dele,
contatos, CPF ou CNPJ na proposta e, às vezes, detalhes do negócio que o cliente não quer
ver circulando. Esta página explica onde esses dados ficam, o que pode sair do computador e
como a app protege o que sai.

!!! note "Isto não é parecer jurídico"
    A app ajuda a cumprir a LGPD, mas quem responde pelo tratamento dos dados é você, o
    consultor. Para os seus contratos e a sua política de privacidade, consulte um
    advogado.

## Onde os dados ficam

- **Tudo no seu computador**, num arquivo: `data/descoberta.db`. A app não tem servidor na
  nuvem, conta nem telemetria, e funciona sem internet.
- **Fora do Git:** `data/`, `*.db` e o `.env` estão no `.gitignore`, e um teste
  (`tests/test_seguranca.py`) confere que o `.env` nunca é versionado.
- **O logotipo** do perfil é regravado sem metadados, como a localização de uma foto de
  celular.
- **Os documentos gerados** (PDF, Word, Markdown) têm dados pessoais. A versão interna do
  relatório tem também os sinais de alerta e as suas anotações, e não deve ir ao cliente.

**Como proteger:** criptografia do disco (BitLocker, FileVault) e backups criptografados.
Veja [Backup e restauração](../guias/backup-e-restauracao.md). Para atender a um pedido de
exclusão, **Excluir** no cliente apaga tudo o que é dele no banco; os backups antigos
seguem a sua política de retenção.

## O que pode sair do computador

Só uma coisa: o **pedido de rascunho ao LLM**, e só se você ligou a API da Anthropic
(`DESCOBERTA_LLM_PROVEDOR=claude`) e pediu um rascunho, depois da sessão. Com o Ollama, o
pedido vai a um programa no seu próprio computador, sem passar por proxy, e nada sai. Com o
LLM desligado, que é o padrão, nada sai nunca.

O pedido leva o contexto da sessão: as respostas, os números já calculados, as saídas da
revisão e o texto que você já escreveu. Por padrão, ele leva o mesmo que a versão cliente
do relatório. **As anotações e os sinais de alerta só vão** se você ligar "Usar anotações
internas como contexto".

## Como a anonimização funciona

Antes de qualquer envio, sempre nesta ordem (`src/descoberta/llm/rascunho.py`):

1. **Anonimizar:** os dados pessoais do pedido viram marcadores.
2. **Conferir:** uma busca final procura o que ainda pareça dado pessoal. Se achar algo, o
   pedido **não sai**: "O pedido ainda tinha dados pessoais depois da anonimização e não
   foi enviado".
3. **Enviar:** o provedor recebe só o texto com os marcadores.
4. **Desfazer, no seu computador:** os marcadores da resposta voltam a ser os dados reais.
   Se a resposta trouxer um marcador que não estava no pedido (inventado pelo modelo), o
   rascunho chega com um alerta.

A troca é feita por **regras fixas**, sem LLM e sem internet
(`src/descoberta/llm/anonimizacao.py`). Há duas fontes:

**Dados que a sessão conhece**, trocados pelo valor:

| Dado | Marcador |
| --- | --- |
| Nome do cliente (contato principal) | `[CLIENTE]` |
| Empresa do cliente | `[EMPRESA]` |
| Representante do cliente na proposta | `[REPRESENTANTE]` |
| Seu nome e sua empresa (perfil) | `[CONSULTOR]`, `[EMPRESA_CONSULTOR]` |
| E-mails, telefone, CPF/CNPJ e cidade do perfil e da proposta | `[EMAIL_1]`, `[TELEFONE_1]`, `[CPF_1]`, `[CNPJ_1]`, `[CIDADE_1]`… |
| Pessoas citadas (a lista da sessão) | `[PESSOA_1]`, `[PESSOA_2]`… |

Nos nomes de pessoas, cada parte também é trocada ("Marcos Pereira" e "o Marcos"). Nos de
empresa, as partes que identificam ("Alvorada"), e não as genéricas ("Construtora",
"Ltda"). As partes só são trocadas com maiúscula inicial: "Rosa" é nome, "rosa" é cor.

**Formatos reconhecíveis**, em qualquer texto: e-mail, CPF, CNPJ (inclusive o
alfanumérico), telefone, CEP e endereço (Rua, Av., Rodovia… seguido do nome). Pontuados,
CPF e CNPJ são sempre trocados. Sem pontuação, só quando os dígitos verificadores conferem,
porque um número qualquer de 11 dígitos não é CPF.

Cada valor tem sempre o **mesmo marcador** no pedido, e a tabela marcador → valor fica no
seu computador.

### O que as regras não pegam

- **Um nome citado de passagem** ("a Cida, da recepção"), que não é o cliente nem o
  consultor e não tem formato reconhecível, **só é trocado se estiver na lista de pessoas
  citadas**. Por isso o painel sugere os nomes que encontra ("Parecem nomes de pessoas"),
  e por isso a prévia existe.
- **Informação sensível sem formato**, como um problema de saúde ou um processo judicial
  descrito em palavras. Ela não é dado de contato, e a app não a reconhece. Evite
  escrevê-la nas respostas, ou deixe-a só nas anotações internas.

## A prévia obrigatória

Antes do **primeiro** rascunho de uma sessão, a app mostra **exatamente** o que sairia: as
instruções, a mensagem e a tabela dos marcadores com os valores reais (que não sai). Você
procura algum nome ou contato que tenha escapado, inclui na lista de pessoas se preciso, e
confirma: **Confirmar: está anonimizado**.

A confirmação vale enquanto os dados conhecidos não mudam. A app guarda só uma "impressão"
deles (um SHA-256 do cliente, do consultor, da proposta e da lista de pessoas). Se um nome
entrar na lista ou um dado do cliente mudar, a prévia precisa ser vista de novo.

## Outras garantias

- **Nunca ao vivo:** com o cronômetro da sessão rodando, a app recusa gerar rascunhos.
- **Rascunhos à parte:** cada sugestão fica numa tabela própria, com o provedor, o modelo e
  a versão do prompt, e só substitui o seu texto se você aceitar.
- **Falha segura:** sem internet, sem chave, com erro na API ou com recusa do modelo, a
  app avisa e não reenvia para outro lugar. O seu texto e o relatório por template
  continuam.
- **A chave da API** fica só na variável de ambiente `ANTHROPIC_API_KEY` (no `.env`) e
  aparece como `**********` em qualquer log ou mensagem. O assistente usado no
  desenvolvimento (Claude Code) está proibido de ler ou editar o `.env`
  (`.claude/settings.json`).

## Como isso é testado

- **Nenhum dado pessoal no pedido:** `tests/llm/test_payload.py` envia o caso Roberto
  inteiro (respostas, anotações, revisão, proposta e perfil) pelo SDK real da Anthropic,
  com um transporte falso, e procura cada dado pessoal do demo no **corpo exato** de cada
  pedido HTTP, sem ligar para maiúsculas e acentos.
- **Nenhum teste sai da máquina:** um fixture bloqueia qualquer conexão para fora, e a
  chave e o provedor são retirados do ambiente dos testes.
- **Histórico do Git:** `scripts/revisar_historico.py` procura CPF, CNPJ, e-mail, telefone,
  CEP e endereço em todas as versões de todos os arquivos já versionados, e o gitleaks
  procura segredos no CI.

## Quem recebe o pedido

Com a API da Anthropic, o pedido anonimizado é tratado pela Anthropic, conforme os termos e
a política de dados da sua conta. Leia-os antes de ativar e, se o seu contrato com o
cliente exigir, informe o uso do serviço. Com o Ollama, o modelo roda no seu computador.

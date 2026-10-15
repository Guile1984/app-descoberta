# App de Descoberta para IA

Uma app para o consultor conduzir, ao vivo, a **sessão de descoberta** com uma pequena ou
média empresa que quer uma solução de inteligência artificial, e sair dela com o
**Relatório de Descoberta** e a **Proposta Comercial** prontos para revisar e enviar.

<!-- Quando o GIF estiver gravado (roteiro em docs/roteiro-gif.md), troque esta linha por:
![Demonstração: sessão do caso Roberto, do primeiro bloco ao relatório](docs/img/demo.gif) -->
> 🎬 Demonstração em vídeo (GIF): em breve.

> [!WARNING]
> **Uso local, por uma pessoa só.** A app roda no seu computador e só aceita conexões
> dele mesmo (`127.0.0.1`). Ela não tem login nem HTTPS. **Não a exponha à rede** (outro
> computador, celular, servidor na nuvem, `--host 0.0.0.0`) sem as medidas do guia de uso
> em produção. Veja [SECURITY.md](SECURITY.md).

## O que a app faz

- **Conduz a sessão** seguindo o *Modelo de Descoberta — Apps de IA para PMEs*: 10 blocos
  de perguntas e o encerramento, com perguntas obrigatórias, aprofundamentos e perguntas
  que só aparecem quando fazem sentido (por exemplo, as de visão computacional).
- **Calcula na hora**, enquanto o cliente fala: custo da dor, prontidão dos dados (score
  de 0 a 15), custo de operação, payback e o score final de viabilidade (0 a 18), com a
  recomendação: seguir, seguir com fase 0 ou não seguir agora.
- **Registra sinais de alerta e anotações** com um clique ou um atalho de teclado; dá para
  conduzir a sessão inteira sem tirar as mãos do teclado.
- **Organiza a revisão pós-sessão**: matriz de riscos, indicadores de sucesso, escopo do
  MVP, próximos passos e os textos do relatório, mostrando o que ainda falta.
- **Gera o Relatório de Descoberta e a Proposta Comercial** em PDF, Word e Markdown, nas
  versões cliente e interna, e registra cada versão enviada com data e um código de
  conferência (hash) no rodapé.
- **Funciona sem internet.** Opcionalmente, depois da sessão, um modelo de linguagem (API
  da Anthropic ou um modelo local) sugere rascunhos dos textos, com os dados pessoais
  trocados por marcadores antes de sair do computador.

## Instalação no Windows, passo a passo

Você precisa de internet só na instalação. Não é preciso instalar o Python: o `uv` cuida
disso sozinho.

**1. Instale o uv** (o programa que baixa e roda a app).
Abra o menu Iniciar, digite **PowerShell**, abra e cole **um** dos dois comandos abaixo.

**Opção A — pelo winget** (o instalador de programas do Windows):

```powershell
winget install --id=astral-sh.uv -e
```

**Opção B — pelo instalador oficial do uv** (use esta se aparecer *"winget não é
reconhecido como nome de cmdlet"*: o winget não vem em todo Windows, como o Windows
Sandbox e alguns computadores de empresa):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Depois, **feche o PowerShell** (o Windows só reconhece o `uv` numa janela nova).

**2. Baixe a app.** No GitHub, clique no botão verde **Code → Download ZIP**. Extraia o
ZIP numa pasta sua, por exemplo `Documentos\app-descoberta`. (Quem usa Git pode fazer
`git clone https://github.com/Guile1984/app-descoberta.git`.)

**3. Abra a app com dois cliques em `iniciar.bat`**, na pasta extraída.

- Na primeira vez, o Windows pode mostrar "O Windows protegeu o computador", porque o
  arquivo veio da internet. Clique em **Mais informações → Executar assim mesmo**.
- Também na primeira vez, uma janela preta mostra o `uv` baixando o Python e as
  bibliotecas (alguns minutos). Das próximas vezes, abre em segundos e sem internet.
- O navegador abre sozinho em **http://127.0.0.1:8000**. Se não abrir, digite esse
  endereço no navegador.
- Se a app já estiver aberta, dois cliques no `iniciar.bat` só abrem o navegador nela (a
  janela nova fecha sozinha em alguns segundos).

**4. Preencha o seu perfil de consultor** (nome, empresa, CPF ou CNPJ, contato, cidade e
logotipo opcional). Ele vai no relatório e na proposta e fica só no seu computador.

**Para fechar a app**, feche a janela preta (ou tecle `Ctrl+C` nela). **Fechar o navegador
não fecha a app**: ela continua rodando enquanto a janela preta estiver aberta. Seus dados
ficam salvos em `data\descoberta.db`, na pasta da app.

## Demonstração: o caso Roberto

O banco de demonstração traz uma sessão completa e fictícia: **Roberto, da Construtora
Alvorada**, que perde 60 horas por mês com chamados de fissura nas obras. Ele nunca toca
nos seus dados reais.

Na pasta da app, clique com o botão direito num espaço vazio → **Abrir no Terminal** e
rode:

```powershell
uv run --no-dev python -m descoberta.demo        # cria (ou recria) data\demo.db
$env:DESCOBERTA_BANCO = "data/demo.db"           # usa o banco de demonstração
uv run --no-dev python -m descoberta             # abre a app no navegador
```

(`--no-dev` instala só o que a app usa, sem as ferramentas de teste, como o
`iniciar.bat`.)

Enquanto o banco de demonstração estiver aberto, uma faixa amarela **"Banco de
demonstração"** aparece no alto de todas as telas.

O que ver, nesta ordem:

1. **Sessão do Roberto**: as respostas de cada bloco e, à direita, os cálculos: 60 h/mês
   de dor, score de dados 4 de 15 (→ fase 0), payback de cerca de 7,7 meses e score final
   12 de 18 → **seguir com fase 0**. Tecle `Ctrl+/` para ver os atalhos.
2. **Revisão pós-sessão →**: riscos (com a matriz 3×3), indicadores, escopo do MVP,
   próximos passos e os textos do relatório, sem nenhuma pendência.
3. **Relatório →**: prévia nas versões cliente e interna; baixe em PDF, Word ou Markdown.
4. **Proposta →**: a proposta da fase 0 e do MVP, com as Condições Gerais.

Para voltar aos seus dados, feche a app e abra de novo pelo `iniciar.bat` (ou numa janela
nova do terminal, onde `DESCOBERTA_BANCO` não está definido).

## Uso no dia a dia

- **Antes da sessão:** cadastre o cliente e abra uma sessão nova. Cada sessão guarda a
  versão do questionário usada.
- **Durante a sessão:** cada campo salva sozinho ao sair dele. Use vírgula para decimais
  (7,5) e ponto para milhar (20.000). Os atalhos (`Ctrl+/`) levam aos blocos, aos sinais,
  às anotações, ao cronômetro e ao encerramento.
- **Depois da sessão:** "Revisão pós-sessão →" mostra o que falta para o relatório.
  Revise os números marcados como **hipótese** (que você assumiu, e não o cliente disse):
  o relatório os destaca.
- **Relatório:** "Registrar versão enviada" guarda o PDF com número de versão, data e
  hash, que aparecem no rodapé de cada página. Para conferir uma cópia assinada, compare
  o rodapé dela com a lista de versões registradas.
- **Proposta Comercial:** criada a partir da revisão e do modelo
  `config/proposta_v1.yaml`, depois editada à parte, sem mudar o relatório. Se o score
  final indicar "não seguir agora", a app avisa antes de criar. O modelo de Condições
  Gerais é um ponto de partida: **revise-o com um advogado** antes de usar com clientes.
  "PDF único" junta o relatório e a proposta num arquivo só.

### Rascunhos por LLM (opcional, depois da sessão)

Na revisão e na proposta, um modelo de linguagem pode sugerir rascunhos dos textos
narrativos. Você revisa e aceita ou descarta: nada muda no seu texto sem aceitar. O LLM
nunca é usado durante a sessão ao vivo nem para cálculos, e a app funciona inteira sem
ele.

**Vem desligado.** Para ativar, copie o arquivo `.env.example` para `.env` (que nunca vai
para o Git) e preencha:

- API da Anthropic: `DESCOBERTA_LLM_PROVEDOR=claude` e a sua chave em
  `ANTHROPIC_API_KEY`. Modelo padrão: `claude-opus-5-5`, em `config/llm.yaml`.
- Modelo local, sem nada sair do computador: instale o [Ollama](https://ollama.com),
  baixe o modelo (`ollama pull llama3.1:8b`) e use `DESCOBERTA_LLM_PROVEDOR=ollama`.
- Para desligar de novo: `DESCOBERTA_LLM_PROVEDOR=desligado` (ou em branco).

O `iniciar.bat` lê o `.env` sozinho, se ele existir (a janela preta mostra
"Configuracoes lidas do arquivo .env"). Feche a app e abra de novo depois de mudar o
`.env`. Cuidado: com as extensões ocultas, o Bloco de Notas salva `.env.txt`; o nome
precisa ser exatamente `.env` (o `iniciar.bat` avisa se encontrar o `.env.txt`).

**Proteção dos dados (LGPD):**

- Antes do envio, nomes, empresa, CPF/CNPJ, telefones, e-mails, endereços e cidade viram
  marcadores (`[CLIENTE]`, `[PESSOA_1]`…); a troca é desfeita no seu computador, na
  resposta.
- Nomes citados de passagem (um funcionário do cliente) só são trocados se estiverem em
  "Pessoas citadas": a app sugere os nomes que encontra; confira a lista.
- Antes do primeiro rascunho, a app mostra a prévia exata do que sai e pede confirmação.
- As anotações do consultor e os sinais de alerta não vão no pedido, a não ser que você
  marque "Usar anotações internas como contexto".
- Sem internet, sem chave ou com erro na API, a app avisa e continua com o seu texto e o
  relatório por template.
- Cada rascunho guarda o provedor, o modelo e a versão do prompt (`prompts/`).

## Cuidados com os dados: backup e criptografia

Tudo o que você registra (clientes, sessões, relatórios, logotipo) fica num arquivo só:
**`data\descoberta.db`**, na pasta da app. São dados pessoais dos seus clientes, então
vale a LGPD.

**Backup**

- Com a app **fechada**, copie o `data\descoberta.db` para outro lugar. Faça isso depois
  de cada sessão importante e, no mínimo, uma vez por semana.
- Guarde a cópia num pendrive ou HD externo **criptografado**, ou compacte-a com senha
  antes de mandar para a nuvem (no [7-Zip](https://www.7-zip.org): formato 7z, criptografia
  AES-256, marcando "Criptografar nomes de arquivos").
- Para restaurar: com a app fechada, coloque a cópia de volta em `data\descoberta.db`.
- Ao atualizar para uma versão nova da app, ela mesma faz uma cópia antes de mudar a
  estrutura do banco (`data\descoberta.antes-....db`). Pode apagar essas cópias depois de
  conferir que está tudo certo.

**Criptografia do disco**

Se o notebook for perdido ou roubado, a criptografia impede que alguém leia o banco
tirando o disco do computador.

- **Windows 11 Pro:** ative o **BitLocker** (menu Iniciar → "Gerenciar o BitLocker").
- **Windows 11 Home:** veja se há **Criptografia do dispositivo** em Configurações →
  Privacidade e segurança.
- **Mac:** ative o **FileVault** (Ajustes do Sistema → Privacidade e Segurança).
- Guarde a **chave de recuperação** fora do notebook (na sua conta Microsoft ou Apple, ou
  impressa num lugar seguro). Sem ela, perder a senha é perder os dados.

## Atualizar para uma versão nova

1. Feche a app e faça um backup do `data\descoberta.db` (veja acima).
2. Baixe o ZIP da versão nova e extraia numa pasta nova.
3. Copie a pasta `data` (e o `.env`, se você usa o LLM) da pasta antiga para a nova.
4. Abra pelo `iniciar.bat` da pasta nova. Se a versão nova mudar a estrutura do banco, a
   app atualiza sozinha ao abrir, guardando uma cópia antes.

## Limitações declaradas

- **Um usuário, um computador.** Não há login, contas nem acesso simultâneo: a app foi
  feita para o consultor, no próprio notebook.
- **Uso local.** Não deve ser exposta à rede sem as medidas do guia de uso em produção
  (Sprint 9). Veja [SECURITY.md](SECURITY.md).
- **Escalabilidade fora do escopo.** O banco é um arquivo SQLite; centenas de clientes e
  sessões funcionam bem (veja `docs/qualidade/medicoes.json`), mas não há suporte a
  equipes nem a servidor.
- **Os documentos são rascunhos para revisão.** Os cálculos seguem regras fixas e
  testadas, mas dependem dos números informados; o relatório e a proposta devem ser lidos
  antes do envio, e o modelo de proposta revisado por um advogado.
- **O LLM só sugere textos**, nunca números, condicionais ou recomendações, e é opcional.
- **Navegadores:** testada automaticamente no Chromium (base do Chrome e do Edge).
- **Testada no Windows e no Linux**; no Mac deve funcionar, mas sem verificação
  automática.

## Transparência: como esta app foi feita

Esta app foi desenvolvida com o **Claude Code** (assistente de programação da Anthropic),
sob **direção e revisão do autor**, Guilherme Ferraz Stauffer. O autor definiu a
metodologia, as regras de negócio e as prioridades, aprovou o plano de cada etapa,
revisou as mudanças e validou a app em uso; o Claude Code escreveu o código e os testes.

O que dá sustentação a isso:

- cada etapa (sprint) começou com um plano aprovado e terminou com revisão do que mudou
  (`CHANGELOG.md` e os pull requests no GitHub);
- os testes foram escritos antes do código; são mais de mil, inclusive no navegador, e
  rodam a cada mudança, junto com verificações de segurança;
- as regras e cálculos estão documentados em `docs/especificacao.md` e reproduzem o caso
  de referência (Roberto) em testes automatizados.

## Licença

- **Código:** [MIT](LICENSE). Pode usar, modificar e distribuir, inclusive comercialmente,
  mantendo o aviso de copyright.
- **Metodologia** (o *Modelo de Descoberta* em `docs/modelo-descoberta.md` e o conteúdo
  do questionário em `config/questionario_v1.yaml`): [CC BY 4.0](LICENSE-METODOLOGIA.md).
  Pode usar e adaptar nas suas sessões, inclusive comercialmente, **dando o crédito** ao
  autor. A licença é diferente porque a metodologia é um texto, e as licenças Creative
  Commons foram feitas para textos: a CC BY garante o crédito em adaptações.
- **Componentes de terceiros** (htmx, fontes DejaVu e as bibliotecas Python): licenças
  próprias, todas permissivas. Veja [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

## Para desenvolvedores

Especificação: `docs/especificacao.md`. Instruções para o Claude Code: `CLAUDE.md`.
Rode os comandos na raiz do projeto (a app lê `config/` e grava em `data/`).

```bash
uv sync                                               # instalar
uv run uvicorn descoberta.web.app:app --reload        # rodar recarregando a cada mudança
uv run pytest --cov=descoberta                        # todos os testes (inclusive e2e)
uv run pytest -m "not e2e"                            # testes rápidos, sem navegador
uv run playwright install chromium                    # navegador dos e2e (uma vez)
uv run ruff check . && uv run ruff format --check .   # lint (inclui as regras S)
uv run pre-commit install                             # ativar os hooks no git
```

O banco vem de `DESCOBERTA_BANCO` (padrão: `data/descoberta.db`). O `uvicorn` escuta em
`127.0.0.1` por padrão: não passe `--host 0.0.0.0`.

**Migrações do banco (Alembic).** A app aplica as migrações sozinha ao ligar
(`repositorio.banco.migrar`), com cópia de segurança antes. Depois de mudar um modelo em
`repositorio/modelos.py`:

```bash
uv run alembic upgrade head                                   # data/alembic-dev.db, descartável
uv run alembic revision --autogenerate --rev-id 0002 -m "o que mudou"
```

Revise o arquivo gerado em `src/descoberta/repositorio/migracoes/versions/` (o
autogenerate não percebe, por exemplo, troca de nome de coluna) e rode os testes: o teste
de "deriva" (`tests/repositorio/test_migracoes.py`) falha se modelos e migrações não
baterem. Bancos de antes do Alembic são reconhecidos pela revisão `0001`.

**Medições e verificações:**

```bash
uv run python scripts/medir_desempenho.py --saida docs/qualidade/medicoes.json
uv run python scripts/revisar_historico.py    # dados pessoais em todo o histórico do Git
```

**E-mail dos commits.** Para não publicar o seu e-mail pessoal nos commits, use o
endereço *noreply* do GitHub (em GitHub → Settings → Emails, marque "Keep my email
addresses private" e copie o endereço `…@users.noreply.github.com` que aparece ali):

```bash
git config user.email "ID+usuario@users.noreply.github.com"   # só neste repositório
git config --global user.email "ID+usuario@users.noreply.github.com"   # em todos
```

Na mesma página, "Block command line pushes that expose my email" impede um push com o
e-mail pessoal por engano. Commits antigos não mudam (reescrever o histórico mudaria
todos os hashes).

Segurança: [SECURITY.md](SECURITY.md). Mudanças: [CHANGELOG.md](CHANGELOG.md).

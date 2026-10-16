# App de Descoberta para IA

[![CI](https://github.com/Guile1984/app-descoberta/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Guile1984/app-descoberta/actions/workflows/ci.yml)
[![Segurança](https://github.com/Guile1984/app-descoberta/actions/workflows/seguranca.yml/badge.svg?branch=main)](https://github.com/Guile1984/app-descoberta/actions/workflows/seguranca.yml)
[![Documentação](https://github.com/Guile1984/app-descoberta/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/Guile1984/app-descoberta/actions/workflows/docs.yml)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue)](LICENSE)
[![Última versão](https://img.shields.io/github/v/release/Guile1984/app-descoberta?label=vers%C3%A3o)](https://github.com/Guile1984/app-descoberta/releases/latest)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FGuile1984%2Fapp-descoberta%2Fmain%2Fpyproject.toml)](pyproject.toml)

Uma app para o consultor conduzir, ao vivo, a **sessão de descoberta** com uma pequena ou
média empresa que quer uma solução de inteligência artificial, e sair dela com o
**Relatório de Descoberta** e a **Proposta Comercial** prontos para revisar e enviar.

📖 **Documentação completa:** <https://guile1984.github.io/app-descoberta/>, com o
tutorial da primeira sessão, guias práticos, referência e as decisões do projeto.

🎓 **Veja a app em ação:** o tutorial [Sua primeira sessão](https://guile1984.github.io/app-descoberta/tutorial/primeira-sessao/)
conduz o caso Roberto do zero até o relatório e a proposta, com capturas de cada tela.

> [!WARNING]
> **Uso local, por uma pessoa só.** A app roda no seu computador e só aceita conexões
> dele mesmo (`127.0.0.1`). Ela não tem login nem HTTPS. **Não a exponha à rede** (outro
> computador, celular, servidor na nuvem, `--host 0.0.0.0`) sem as medidas do [guia de uso
> em produção](https://guile1984.github.io/app-descoberta/explicacao/uso-em-producao/). Veja [SECURITY.md](SECURITY.md).

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

Para aprender fazendo, siga o tutorial [Sua primeira sessão](https://guile1984.github.io/app-descoberta/tutorial/primeira-sessao/).
Em resumo:

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
narrativos, que você aceita ou descarta. Vem **desligado**, e a app funciona inteira sem
ele. Nunca é usado durante a sessão ao vivo nem para cálculos. Antes de qualquer envio, os
dados pessoais viram marcadores (`[CLIENTE]`, `[PESSOA_1]`…), e a app mostra a prévia
exata do que sai.

Para ativar (API da Anthropic ou um modelo local com o Ollama), copie o `.env.example` para
`.env` e siga o guia [Configurar o LLM](https://guile1984.github.io/app-descoberta/guias/configurar-llm/). Como a
anonimização funciona: [Privacidade, LGPD e anonimização](https://guile1984.github.io/app-descoberta/explicacao/privacidade-lgpd/).

## Cuidados com os dados: backup e criptografia

Tudo o que você registra fica num arquivo só: **`data\descoberta.db`**, na pasta da app.
São dados pessoais dos seus clientes, então vale a LGPD.

- **Backup:** com a app **fechada**, copie o `data\descoberta.db` para um lugar
  **criptografado**, depois de cada sessão importante e no mínimo uma vez por semana. Para
  restaurar, com a app fechada, coloque a cópia de volta no lugar.
- **Criptografia do disco:** ative o BitLocker (Windows) ou o FileVault (Mac), para ninguém
  ler o banco tirando o disco de um notebook perdido.

Passo a passo, inclusive como compactar com senha e restaurar com segurança:
[Backup e restauração](https://guile1984.github.io/app-descoberta/guias/backup-e-restauracao/).

## Atualizar para uma versão nova

Feche a app, faça um backup, extraia a versão nova numa pasta nova e copie para ela a pasta
`data` (e o `.env`, se você usa o LLM). Se a versão nova mudar a estrutura do banco, a app
atualiza sozinha ao abrir, guardando uma cópia antes. Detalhes:
[Atualizar a app](https://guile1984.github.io/app-descoberta/guias/atualizar-a-app/).

## Limitações declaradas

- **Um usuário, um computador.** Não há login, contas nem acesso simultâneo: a app foi
  feita para o consultor, no próprio notebook.
- **Uso local.** Não deve ser exposta à rede sem as medidas do
  [guia de uso em produção](https://guile1984.github.io/app-descoberta/explicacao/uso-em-producao/). Veja [SECURITY.md](SECURITY.md).
- **Escalabilidade fora do escopo.** O banco é um arquivo SQLite; centenas de clientes e
  sessões funcionam bem (veja as [medições](https://guile1984.github.io/app-descoberta/qualidade/evidencias/)), mas não há
  suporte a equipes nem a servidor.
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

Como preparar o ambiente, rodar os testes e mandar uma contribuição:
[CONTRIBUTING.md](CONTRIBUTING.md). Comandos e variáveis de ambiente:
[referência](https://guile1984.github.io/app-descoberta/referencia/ambiente-e-comandos/). Arquitetura e decisões:
[explicação](https://guile1984.github.io/app-descoberta/explicacao/arquitetura/). Especificação: `docs/especificacao.md`.
Instruções para o Claude Code: `CLAUDE.md`.

```bash
uv sync && uv run pytest -m "not e2e"     # instalar e rodar os testes rápidos
```

Segurança: [SECURITY.md](SECURITY.md). Mudanças: [CHANGELOG.md](CHANGELOG.md). Código de
conduta: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

[Documentação](https://guile1984.github.io/app-descoberta/) ·
[Como contribuir](CONTRIBUTING.md) ·
[Segurança](SECURITY.md) ·
[Licença](LICENSE)

Desenvolvido por [Guilherme Ferraz Stauffer](https://github.com/Guile1984).

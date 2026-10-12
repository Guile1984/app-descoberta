# App de Descoberta para IA

App local para conduzir ao vivo sessões de descoberta com clientes PME que desejam
soluções de IA e gerar o Relatório de Descoberta. Veja `docs/especificacao.md`.

> Em desenvolvimento. Projeto desenvolvido com Claude Code sob direção e revisão do autor.

## Comandos

```bash
uv sync                                   # instalar
uv run pytest --cov=descoberta            # testes
uv run ruff check . && uv run ruff format --check .   # lint
uv run pre-commit install                 # ativar hooks no git
```

## Rodar a app

Rode os comandos na raiz do projeto (a app lê `config/` e grava em `data/`).

```bash
uv run uvicorn descoberta.web.app:app --reload   # abre em http://127.0.0.1:8000
```

O banco real fica em `data/descoberta.db` (fora do Git). Para usar outro arquivo, defina a
variável `DESCOBERTA_BANCO`.

### Demonstração com o caso Roberto

```powershell
uv run python -m descoberta.demo                 # (re)cria data/demo.db
$env:DESCOBERTA_BANCO = "data/demo.db"           # PowerShell
uv run uvicorn descoberta.web.app:app --reload
```

No Bash: `DESCOBERTA_BANCO=data/demo.db uv run uvicorn descoberta.web.app:app --reload`.
O comando de demonstração recria só o `data/demo.db` e nunca toca no banco real.
Na sessão do Roberto, o botão "Revisão pós-sessão →" abre a revisão já preenchida (riscos,
indicadores, escopo do MVP, próximos passos e textos do relatório).

### Relatório

O botão "Relatório →" (na sessão ou na revisão) mostra a prévia nas versões cliente e
interna e baixa o rascunho em PDF, Word ou Markdown, tudo sem internet. "Registrar versão
enviada" guarda o PDF com número de versão, data e hash SHA-256, que aparecem no rodapé de
cada página: compare o rodapé da cópia assinada com a lista de versões registradas.

### Perfil do consultor

No primeiro uso, a tela inicial pede o perfil do consultor (nome, empresa, CPF ou CNPJ,
contato, cidade/UF e logotipo opcional). Ele vai no relatório e na proposta, inclusive no
bloco de assinatura do consultor, e fica só no banco local. Para mudar depois: menu
"Perfil". No banco de demonstração, o consultor é fictício e os documentos avisam isso.

### Proposta Comercial

O botão "Proposta →" (na revisão ou no relatório) cria a proposta como cópia do modelo
`config/proposta_v1.yaml` e da revisão; depois ela é editada à parte, sem mudar o
relatório. Se o score final indicar "não seguir agora", a app avisa antes de criar.

- As Condições Gerais vêm do modelo. Em cada proposta dá para ajustar o texto de uma
  cláusula ou excluir as removíveis, sem mudar o modelo.
- O modelo é um ponto de partida: revise-o com um advogado antes de usar com clientes.
- "Registrar versão enviada" guarda o PDF da proposta com numeração própria, hash no
  rodapé e as cláusulas congeladas.
- "PDF único" junta o relatório (cliente) e a proposta num arquivo só; cada parte mantém o
  próprio rodapé e hash.

### Rascunhos por LLM (opcional, depois da sessão)

Na revisão e na proposta, um LLM pode sugerir rascunhos dos textos narrativos (resumo
executivo, frase-problema, fluxos, justificativa, recomendação, contexto da proposta e
objetivo de cada fase). Você revisa e aceita ou descarta: nada muda no seu texto sem
aceitar. O LLM nunca é usado durante a sessão ao vivo (com o cronômetro rodando) nem para
cálculos, e a app funciona inteira sem ele.

**Vem desligado.** Para ativar, copie o `.env.example` para `.env` (que fica fora do Git),
preencha e rode a app lendo o `.env`:

```bash
uv run --env-file .env uvicorn descoberta.web.app:app --reload
```

- API da Anthropic: `DESCOBERTA_LLM_PROVEDOR=claude` e a chave em `ANTHROPIC_API_KEY`
  (só no `.env`, nunca no código nem no Git). Modelo padrão: `claude-opus-5-5`, em
  `config/llm.yaml`.
- Modelo local, sem nada sair da máquina: instale o [Ollama](https://ollama.com), baixe o
  modelo (`ollama pull llama3.1:8b`) e use `DESCOBERTA_LLM_PROVEDOR=ollama`.
- Para desligar de novo: `DESCOBERTA_LLM_PROVEDOR=desligado` (ou em branco).

**Proteção dos dados (LGPD):**

- Antes do envio, nomes, empresa, CPF/CNPJ, telefones, e-mails, endereços e cidade viram
  marcadores (`[CLIENTE]`, `[PESSOA_1]`…); a troca é desfeita na sua máquina, na resposta.
- Nomes citados de passagem (um funcionário do cliente) só são trocados se estiverem em
  "Pessoas citadas": a app sugere os nomes que encontra; confira a lista.
- Antes do primeiro rascunho, a app mostra a prévia exata do que sai e pede confirmação.
  A prévia vale até a lista de pessoas ou os dados do cliente mudarem.
- Como na versão cliente do relatório, as anotações do consultor e os sinais de alerta não
  vão no pedido, a não ser que você marque "Usar anotações internas como contexto" (o
  conteúdo delas pode aparecer no texto gerado).
- Sem internet, sem chave ou com erro na API, a app avisa e continua com o seu texto e o
  relatório por template.
- Cada rascunho guarda o provedor, o modelo e a versão do prompt (`prompts/`).

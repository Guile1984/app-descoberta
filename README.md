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

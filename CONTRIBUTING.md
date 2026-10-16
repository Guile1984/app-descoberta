# Como contribuir

Obrigado pelo interesse! Este é um projeto pessoal, mantido por uma pessoa, e toda ajuda é
bem-vinda: relatar um problema, sugerir uma melhoria, corrigir a documentação ou mandar
código. Ao participar, você concorda com o [Código de Conduta](CODE_OF_CONDUCT.md).

A documentação completa (uso, referência e decisões de arquitetura) está no site:
<https://guile1984.github.io/app-descoberta/>.

## Relatar um problema ou sugerir uma melhoria

Abra uma [issue](https://github.com/Guile1984/app-descoberta/issues/new/choose) e escolha o
modelo: **Problema** ou **Melhoria**.

- **Nunca cole dados reais de clientes** (nomes, contatos, respostas, relatórios). Use os
  dados fictícios do banco de demonstração: `uv run --no-dev python -m descoberta.demo`.
- **Vulnerabilidades de segurança não vão em issue pública.** Siga o
  [SECURITY.md](SECURITY.md) (relato privado pelo GitHub).

## Preparar o ambiente

Você precisa do [uv](https://docs.astral.sh/uv/) e do Git. O `uv` instala o Python certo
sozinho.

```bash
git clone https://github.com/Guile1984/app-descoberta.git
cd app-descoberta
uv sync                                  # dependências da app e de desenvolvimento
uv run playwright install chromium       # navegador dos testes e2e (uma vez por máquina)
uv run pre-commit install                # hooks de formatação e lint no git commit
```

Rode os comandos na raiz do projeto: a app lê `config/` e `prompts/` e grava em `data/`.

| Para | Comando |
| --- | --- |
| Rodar a app recarregando a cada mudança | `uv run uvicorn descoberta.web.app:app --reload` |
| Usar o banco de demonstração | `uv run python -m descoberta.demo` e `DESCOBERTA_BANCO=data/demo.db` |
| Todos os testes (inclusive no navegador) | `uv run pytest --cov=descoberta` |
| Só os testes rápidos | `uv run pytest -m "not e2e"` |
| Lint e formatação | `uv run ruff check . && uv run ruff format --check .` |
| Ver a documentação | `uv run --group docs mkdocs serve` |
| Compilar a documentação como o CI | `uv run --group docs mkdocs build --strict` |

O `uvicorn` escuta em `127.0.0.1` por padrão. **Não** passe `--host 0.0.0.0`: a app não
tem login (veja o [guia de uso em produção](https://guile1984.github.io/app-descoberta/explicacao/uso-em-producao/)).
A lista completa de comandos e variáveis está na
[referência](https://guile1984.github.io/app-descoberta/referencia/ambiente-e-comandos/).

## Como o projeto trabalha

- **Testes antes do código (TDD).** Escreva o teste que falha, depois a implementação.
  Nenhum teste chama a rede nem um LLM de verdade: um fixture bloqueia conexões para fora,
  e há provedores falsos em `src/descoberta/llm/falso.py`.
- **Tudo passando antes do PR:** `uv run pytest` e `uv run ruff check .`. O CI roda também
  os testes no Windows, o `pip-audit`, o gitleaks e a compilação da documentação com a
  verificação de links.
- **Um assunto por PR**, com a descrição pronta no modelo (o que muda, por quê, como testar).
- **CHANGELOG:** acrescente a mudança em `## [Não lançado]`, no formato
  [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
- **Português do Brasil** nos textos, nas mensagens da tela e nos commits. Nomes no código
  também em português, como no resto do projeto.

### Regras de arquitetura

As decisões e o porquê de cada uma estão em
[Arquitetura e decisões](https://guile1984.github.io/app-descoberta/explicacao/arquitetura/).
As principais:

- **Dependências apontam para dentro:** `dominio` não importa `web`, `repositorio` nem
  `llm`, e as outras camadas têm regras parecidas. `tests/test_estrutura.py` confere.
- **O questionário nunca é escrito no código:** vem do YAML (`config/`), validado com
  Pydantic. O mesmo vale para o modelo da proposta e para os prompts.
- **Números em campos próprios**, nunca extraídos do texto; contas só em `dominio`, e o
  relatório usa os números do painel.
- **O LLM não faz contas, condicionais nem nenhuma lógica determinística.** Ele só sugere
  textos, e o consultor aceita ou descarta.
- **Sem React nem build de frontend:** FastAPI, Jinja2 e HTMX, com JavaScript mínimo.
- **Dependência nova precisa de justificativa** no PR e de licença permissiva
  (`tests/test_licencas.py` barra as outras).
- **Mudou um modelo do banco?** Crie a migração:
  `uv run alembic revision --autogenerate --rev-id NNNN -m "o que mudou"` e revise o
  arquivo gerado. Veja
  [Atualizar a app](https://guile1984.github.io/app-descoberta/guias/atualizar-a-app/#para-quem-desenvolve-criar-uma-migracao).

### Dados pessoais e segredos

- Testes, exemplos e capturas de tela usam **só dados fictícios** (o caso Roberto do demo,
  domínios `example.com`, documentos de teste).
- A chave da API fica só no `.env`, que nunca vai para o Git.
- Antes de um PR grande, rode `uv run python scripts/revisar_historico.py`: ele procura
  CPF, CNPJ, e-mail, telefone, CEP e endereço em todo o histórico do Git.

## Documentação

O site fica em `docs/` (MkDocs com o tema Material) e segue o modelo
[Diátaxis](https://diataxis.fr/). Ponha cada texto na parte certa:

| Parte | Pasta | Para |
| --- | --- | --- |
| Tutorial | `docs/tutorial/` | aprender fazendo, do começo ao fim |
| Guias práticos | `docs/guias/` | uma tarefa específica |
| Referência | `docs/referencia/` | consultar fatos: campos, fórmulas, comandos |
| Explicação | `docs/explicacao/` | entender o porquê |

- **A documentação descreve o código de verdade.** Ao descrever um comportamento, confira no
  código. `tests/test_documentacao.py` confere as páginas de referência (atalhos, campos
  do YAML, tabelas, variáveis de ambiente, opções de linha de comando, faixas dos scores)
  e falha quando algo fica de fora.
- **Página nova:** inclua-a no `nav` do `mkdocs.yml`. O teste falha se ela ficar fora do
  menu sem estar em `not_in_nav`.
- **A interface mudou?** Refaça as capturas: `uv run python scripts/capturar_telas.py`
  (usa só o banco de demonstração).
- O README é a porta de entrada: instalação, demonstração e o essencial. Os detalhes vão
  para o site.

## E-mail dos commits

Para não publicar o seu e-mail pessoal nos commits, use o endereço *noreply* do GitHub: em
GitHub → Settings → Emails, marque "Keep my email addresses private" e copie o endereço
`…@users.noreply.github.com`:

```bash
git config user.email "ID+usuario@users.noreply.github.com"
```

Na mesma página, "Block command line pushes that expose my email" impede um push com o
e-mail pessoal por engano.

## Licença das contribuições

Ao contribuir, você concorda que a sua contribuição fica sob a licença do que ela altera:
**MIT** para o código e **CC BY 4.0** para a metodologia (`docs/modelo-descoberta.md` e o
conteúdo do questionário).

## Uso de IA

Este projeto foi desenvolvido com o Claude Code, sob direção e revisão do autor.
Contribuições feitas com ajuda de IA são bem-vindas, desde que você as tenha revisado,
entenda o que mudou e os testes passem, como em qualquer outra.

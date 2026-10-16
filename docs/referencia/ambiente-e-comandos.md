# Variáveis de ambiente e comandos

Rode todos os comandos **na pasta da app** (a raiz do projeto): a app lê `config/` e
`prompts/` e grava em `data/` a partir de onde foi aberta.

## Variáveis de ambiente

| Variável | Padrão | O que faz |
| --- | --- | --- |
| `DESCOBERTA_BANCO` | `data/descoberta.db` | Arquivo do banco. O demonstrativo usa `data/demo.db`. Com um arquivo chamado `demo.db`, todas as telas mostram a faixa "Banco de demonstração". |
| `DESCOBERTA_LLM_PROVEDOR` | em branco (vale o `config/llm.yaml`, que vem com `desligado`) | `claude`, `ollama` ou `desligado`. Preenchida, vale mais que o campo `provedor` do `config/llm.yaml`. Outro valor impede a app de ligar, com a mensagem do que usar. |
| `ANTHROPIC_API_KEY` | em branco | Chave da API da Anthropic, só para `DESCOBERTA_LLM_PROVEDOR=claude`. É lida na hora de usar, e nunca aparece em log, mensagem de erro ou página: é exibida como `**********`. |

**O arquivo `.env`.** O jeito mais simples de definir as variáveis é copiar o
`.env.example` para `.env` e preencher. O `.env` está no `.gitignore` e nunca vai para o
Git. O `iniciar.bat` lê o `.env` sozinho, se ele existir; na linha de comando, use
`uv run --env-file .env …`. Depois de mudar o `.env`, feche a app e abra de novo. Veja
[Configurar o LLM](../guias/configurar-llm.md).

**Definir só nesta janela do terminal** (some quando a janela fecha):

=== "PowerShell"

    ```powershell
    $env:DESCOBERTA_BANCO = "data/demo.db"
    ```

=== "Bash"

    ```bash
    export DESCOBERTA_BANCO=data/demo.db
    ```

## Usar a app

| Comando | O que faz |
| --- | --- |
| `iniciar.bat` (dois cliques) | Abre a app no Windows: escuta só em `127.0.0.1`, abre o navegador quando ela está pronta e lê o `.env`, se existir. Instala só o que a app usa (`uv run --no-dev --frozen`). Aceita as mesmas opções do comando abaixo. |
| `uv run --no-dev python -m descoberta` | O mesmo, pelo terminal, em qualquer sistema. |
| `uv run --no-dev python -m descoberta.demo` | Cria (ou recria do zero) o banco de demonstração `data/demo.db`, com o caso Roberto. Aceita outro caminho: `… descoberta.demo outro.db`. O banco real nunca é tocado. |

**Opções de `python -m descoberta`:**

| Opção | Padrão | O que faz |
| --- | --- | --- |
| `--porta` | 8000 | Porta da app. Use outra se a 8000 estiver ocupada por outro programa (a mensagem de erro sugere a próxima). |
| `--sem-navegador` | desligado | Não abre o navegador sozinho. |

Não há opção para mudar o endereço: a app escuta **só** em `127.0.0.1`, de propósito (veja
[Uso em produção](../explicacao/uso-em-producao.md)).

**Se a app já estiver aberta** na mesma porta, o comando não abre uma segunda: avisa "A app
já está aberta", abre o navegador nela e a janela nova fecha sozinha em 5 segundos. Para
saber se a porta está com a própria app (e não com outro programa), ele pergunta no
endereço `/_identidade`.

**Para encerrar:** feche a janela preta ou tecle `Ctrl+C` nela. Fechar o navegador não
encerra a app.

## Desenvolvimento

Estes comandos instalam também as ferramentas de teste (grupo `dev`, o padrão do `uv`).

| Comando | O que faz |
| --- | --- |
| `uv sync` | Instala tudo o que o projeto usa, nas versões exatas do `uv.lock`. |
| `uv run uvicorn descoberta.web.app:app --reload` | Roda a app recarregando a cada mudança no código. O `uvicorn` escuta em `127.0.0.1` por padrão: **não** passe `--host 0.0.0.0`. |
| `uv run pytest --cov=descoberta` | Todos os testes, inclusive os do navegador (e2e), com cobertura. |
| `uv run pytest -m "not e2e"` | Os testes rápidos, sem navegador. |
| `uv run playwright install chromium` | Baixa o navegador dos testes e2e (uma vez por máquina). |
| `uv run ruff check .` | Lint, inclusive as regras de segurança (S, do flake8-bandit). |
| `uv run ruff format --check .` | Confere a formatação. |
| `uv run pre-commit install` | Ativa os hooks no Git (formatação, lint, arquivos grandes, chaves privadas). |

**Migrações do banco** (depois de mudar `src/descoberta/repositorio/modelos.py`):

| Comando | O que faz |
| --- | --- |
| `uv run alembic upgrade head` | Leva o banco **descartável** `data/alembic-dev.db` à última revisão. A linha de comando do Alembic ignora `DESCOBERTA_BANCO` de propósito e nunca mexe no banco real. |
| `uv run alembic revision --autogenerate --rev-id 0002 -m "o que mudou"` | Gera a migração nova comparando os modelos com o banco descartável. Revise o arquivo gerado. |

Detalhes em [Atualizar a app](../guias/atualizar-a-app.md#para-quem-desenvolve-criar-uma-migracao).

**Documentação** (grupo `docs`, à parte):

| Comando | O que faz |
| --- | --- |
| `uv run --group docs mkdocs serve` | Abre o site da documentação em `http://127.0.0.1:8000`, atualizando a cada mudança. Se a app estiver aberta na 8000, use `mkdocs serve -a 127.0.0.1:8001`. |
| `uv run --group docs mkdocs build --strict` | Compila o site em `site/`, falhando em qualquer aviso (link quebrado, página fora do menu). É o que o CI roda. |

**Scripts de verificação:**

| Comando | O que faz |
| --- | --- |
| `uv run python scripts/medir_desempenho.py` | Mede tempos de resposta, de geração de documentos, memória e volume, com bancos temporários. |
| `uv run python scripts/revisar_historico.py` | Procura dados pessoais (CPF, CNPJ, e-mail, telefone, CEP, endereço) em todas as versões de todos os arquivos do histórico do Git. Mostra o resultado só no terminal. |
| `uv run python scripts/capturar_telas.py` | Refaz as capturas de tela desta documentação a partir do banco de demonstração. |

Opções de `scripts/medir_desempenho.py`:

| Opção | Padrão | O que faz |
| --- | --- | --- |
| `--repeticoes` | 30 | Quantas vezes cada operação é medida. |
| `--clientes` | 500 | Clientes do volume sintético. |
| `--sessoes-por-cliente` | 2 | Sessões por cliente no volume sintético. |
| `--saida` | — | Grava o resultado em JSON (por exemplo, `docs/qualidade/medicoes.json`). |

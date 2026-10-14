# Avisos de terceiros (Third-party notices)

O código da App de Descoberta está sob a licença MIT (`LICENSE`); a metodologia, sob
CC BY 4.0 (`LICENSE-METODOLOGIA.md`). Este arquivo lista os componentes de terceiros e as
licenças deles. O teste `tests/test_licencas.py` confere esta lista.

## Incluídos no repositório

Estes arquivos são de terceiros e vão junto com o código, sem modificação.

### htmx 2.0.4

- Arquivo: `src/descoberta/web/static/htmx.min.js` (cópia do `dist/htmx.min.js` oficial).
- SHA-256: `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`
- Origem: https://github.com/bigskysoftware/htmx/tree/v2.0.4
- Licença: Zero-Clause BSD (0BSD). Permite usar, copiar, modificar e distribuir para
  qualquer fim, sem exigir nem o aviso; ele fica aqui por transparência.

```
Zero-Clause BSD
=============

Permission to use, copy, modify, and/or distribute this software for
any purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED “AS IS” AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE
FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY
DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```

### Fontes DejaVu Sans (normal e negrito)

- Arquivos: `src/descoberta/relatorio/fontes/DejaVuSans.ttf` e `DejaVuSans-Bold.ttf`,
  usadas nos PDFs (relatório e proposta) para acentos e símbolos.
- Origem: https://dejavu-fonts.github.io/
- Licença: Bitstream Vera Fonts License, com a licença das fontes Arev (mudanças do
  DejaVu em domínio público). Texto completo, que acompanha as fontes:
  `src/descoberta/relatorio/fontes/LICENSE-DejaVu.txt`.
- Compatível com a distribuição sob MIT. Condições respeitadas: o aviso de copyright e
  licença vai junto com as fontes; elas não são vendidas sozinhas (só como parte de um
  programa maior); não foram modificadas (se fossem, teriam de mudar de nome, sem
  "Bitstream" nem "Vera"). Embutir as fontes nos PDFs gerados é permitido.

## Dependências Python (instaladas pelo uv, não incluídas no repositório)

Baixadas do PyPI pelo `uv sync`, nas versões exatas do `uv.lock`. Inclui as dependências
das dependências; algumas só são instaladas em certos sistemas.

| Pacote | Licença |
| --- | --- |
| alembic | MIT |
| annotated-doc | MIT |
| annotated-types | MIT |
| anthropic | MIT |
| anyio | MIT |
| charset-normalizer | MIT |
| click | BSD-3-Clause |
| docstring-parser | MIT |
| fastapi | MIT |
| h11 | MIT |
| httpcore2 | BSD-3-Clause |
| httpx2 | BSD-3-Clause |
| httpx2-jsfetch | BSD-3-Clause (só no navegador/WebAssembly; não instalado no Windows) |
| idna | BSD-3-Clause |
| jinja2 | BSD-3-Clause |
| jiter | MIT |
| lxml | BSD-3-Clause |
| mako | MIT |
| markupsafe | BSD-3-Clause |
| opentelemetry-api | Apache-2.0 |
| pillow | MIT-CMU |
| pydantic | MIT |
| pydantic-core | MIT |
| pypdf | BSD-3-Clause |
| python-docx | MIT |
| python-multipart | Apache-2.0 |
| pyyaml | MIT |
| reportlab | BSD |
| sniffio | MIT OR Apache-2.0 |
| sqlalchemy | MIT |
| sqlmodel | MIT |
| starlette | BSD-3-Clause |
| truststore | MIT |
| typing-extensions | PSF-2.0 |
| typing-inspection | MIT |
| uvicorn | BSD-3-Clause |

Todas são permissivas e compatíveis com MIT.

### Ferramentas de desenvolvimento

Usadas só para testar e verificar o código (pytest, Playwright, ruff, pre-commit e as
dependências delas); não fazem parte da app. Todas permissivas, com duas observações:

- `certifi` e `pytest-base-url`: MPL-2.0 ("copyleft fraco" por arquivo: só obrigaria a
  publicar mudanças nos arquivos dessas bibliotecas, que não são modificados).
- `text-unidecode` (vem com o pytest-playwright): dupla licença, Artistic ou GPL-2.0+;
  usada só nos testes e nunca distribuída, vale a opção Artistic.

## Serviços externos opcionais

Se o consultor ligar o rascunho por LLM, a app conversa com a API da Anthropic (termos
de uso da Anthropic) ou com o Ollama local (MIT; os modelos têm licenças próprias). Nada
disso é incluído no repositório.

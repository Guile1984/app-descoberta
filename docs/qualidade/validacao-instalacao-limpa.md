# Validação: caso Roberto numa instalação do zero

Feita em 14/10/2026 (Sprint 8), seguindo **só o README**, numa pasta nova, a partir do
ZIP da branch baixado do GitHub (o mesmo caminho do passo 2 da instalação).

## Ambiente

- Windows 11 Pro 10.0.26200, PowerShell 5.1, uv 0.12.23.
- Para simular um computador que nunca rodou a app: cache do uv vazio
  (`UV_CACHE_DIR`) e nenhuma instalação de Python do uv (`UV_PYTHON_INSTALL_DIR`), ambos
  em pastas novas. O `uv` em si já estava instalado (passo 1 não repetido).
- Porta 8000 livre; nenhuma variável `DESCOBERTA_*` definida.

## Passo a passo e resultado

| Passo do README | Resultado |
| --- | --- |
| 2. Baixar o ZIP e extrair | `iniciar.bat` chega com finais de linha do Windows (CRLF) |
| 3. Abrir com o `iniciar.bat` (primeira vez) | Baixou o Python e as bibliotecas e abriu em **26 s**; só as bibliotecas da app, sem as ferramentas de teste |
| 3. Abrir de novo | **2,4 s** |
| 3. Sem o `uv` instalado | Mensagem "O uv não está instalado. Veja o passo 1 da instalação no README.md." |
| 4. Primeiro uso | A tela inicial pede o perfil do consultor; `data\descoberta.db` criado |
| Rede (conferido com o `iniciar.bat` do repositório, na porta 8765) | Escuta só em `127.0.0.1`; pelo IP da rede local, sem conexão; com outro `Host`, HTTP 400 |
| Demonstração (3 comandos) | Lista com a Construtora Alvorada; sessão com **60 h/mês, 4 de 15, 7,7 meses, 12 de 18, Seguir com fase 0**; revisão "Nada falta"; relatório em PDF (77 KB), DOCX (50 KB) e Markdown (21 KB); proposta em PDF |
| Banco real | Intacto durante a demonstração (a demo usa `data\demo.db`) |
| Caso Roberto de ponta a ponta, pela tela, num banco vazio | `tests/e2e/test_caso_roberto_ponta_a_ponta.py` passou na pasta do ZIP: perfil → cliente → sessão → revisão sem pendências → relatório → versão registrada, com o hash do rodapé em todas as páginas do PDF |
| Migrações | Os testes das migrações passaram na pasta do ZIP; uma cópia do `data/demo.db` antigo (de antes do Alembic) foi reconhecida, com as 125 linhas iguais e `integrity_check` ok |

## Problemas encontrados e corrigidos durante a validação

1. **Erro "O sistema não pode encontrar o caminho especificado"** ao abrir pelo
   `iniciar.bat`: o arquivo tinha um redirecionamento do Bash (`>/dev/null`) no lugar do
   do Windows (`>nul`). Corrigido, com teste.
2. **A primeira abertura baixava as ferramentas de teste** (Playwright, ruff, pytest),
   que quem só usa a app não precisa: o `iniciar.bat` e os comandos do README passaram a
   usar `uv run --no-dev --frozen`/`--no-dev`. A primeira abertura caiu de 38 s para 26 s.
3. **A mensagem do comando de demonstração** mandava usar `uvicorn --reload` (comando de
   desenvolvimento); agora mostra o mesmo comando do README.
4. **A linha de comando do Alembic** (só para quem desenvolve) usava a variável
   `DESCOBERTA_BANCO` e podia migrar o banco real sem cópia de segurança; agora usa só o
   banco descartável do `alembic.ini`.

## Pendente (Gui)

- [x] Repetir os passos 1 a 4 e a demonstração num Windows realmente novo, sem o `uv`
  (**Windows Sandbox**). Feito pelo Gui em 15/10/2026: o README funcionou do zero. O
  `winget` não existia no Sandbox; só o instalador oficial do uv pelo PowerShell
  funcionou (o README passou a mostrar as duas opções em destaque). Ajustes pedidos e
  feitos: o `iniciar.bat` explica como encerrar e reconhece a app já aberta; faixa
  "Banco de demonstração" em todas as telas; aviso de `.env.txt`.
- [ ] Investigar a lentidão de `tests/relatorio/test_exportar.py` no job Windows do CI
  (~3,5 min; veja `evidencias.md`, Testabilidade).
- [ ] Ler o relatório e a proposta do Roberto gerados (PDF e DOCX), como cliente leria, e
  registrar o que mudaria. É o "relatório revisado" do critério de aceite do Sprint 8.
- [x] ~~Gravar o GIF~~: substituído pelo link para o tutorial do site, com capturas de
  tela. O roteiro (`docs/roteiro-gif.md`) ficou como opcional.

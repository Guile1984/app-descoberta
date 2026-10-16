# Tornar o repositório público: lista manual

Passos que só o dono do repositório faz, no GitHub (Sprint 8). Siga na ordem: os
primeiros garantem que nada sensível fica exposto antes de abrir.

## Antes de abrir

- [ ] **Merge do PR do Sprint 8** com todos os jobs verdes: `qualidade`, `testes-windows`
  (CI) e `pip-audit`, `gitleaks` (Segurança).
- [ ] **Conferir a revisão do histórico** (`docs/qualidade/revisao-historico.md`): em
  especial, confirmar que Roberto, Marcos, Cida e Construtora Alvorada são fictícios.
- [ ] **E-mail dos commits** (decisão D3): em github.com → *Settings → Emails*, marcar
  **Keep my email addresses private** e **Block command line pushes that expose my
  email**. No computador, na pasta do projeto:
  `git config user.email "132632837+Guile1984@users.noreply.github.com"`
  (o endereço exato aparece nessa mesma página do GitHub).
- [ ] **Branches antigas** (opcional): apagar as já mergeadas (`sprint-3-persistencia` …
  `sprint-7-llm`, `correcao-ci`) em *Code → Branches*. O histórico continua na `main`.
- [ ] **Actions**: em *Settings → Actions → General*, deixar **Workflow permissions** em
  *Read repository contents and packages permissions* e desmarcar *Allow GitHub Actions
  to create and approve pull requests*.

## Abrir

- [ ] *Settings → General → Danger Zone →* **Change repository visibility → Public**.

## Logo depois de abrir

- [ ] *Settings → Code security* (*Advanced Security*):
  - [ ] **Private vulnerability reporting**: *Enable* (é o canal do `SECURITY.md`);
  - [ ] **Dependency graph**: ligado;
  - [ ] **Dependabot alerts** e **Dependabot security updates**: *Enable*;
  - [ ] **Secret scanning** e **Push protection**: *Enable* (grátis em repositório
    público);
  - [ ] **Code scanning → CodeQL** (opcional): *Set up → Default*.
- [ ] **Proteção da `main`**: *Settings → Rules → Rulesets → New branch ruleset*:
  - nome: `main`; *Enforcement status*: **Active**; *Target branches*: **Include default
    branch**;
  - **Restrict deletions** e **Block force pushes**: marcados;
  - **Require a pull request before merging**, com **Required approvals: 0** (sendo o
    único autor, você não pode aprovar o próprio PR; o PR continua obrigatório e passa
    pelo CI);
  - **Require status checks to pass**, marcando **Require branches to be up to date
    before merging** e adicionando: `qualidade`, `testes-windows`, `pip-audit`,
    `gitleaks` (eles aparecem na busca depois de rodarem uma vez);
  - *Bypass list*: vazia (nem o administrador pula as regras).
- [ ] **About** (engrenagem na página inicial do repositório): descrição ("App local para
  conduzir sessões de descoberta de IA com PMEs e gerar o relatório e a proposta"),
  tópicos (`ia`, `pme`, `descoberta`, `consultoria`, `fastapi`, `htmx`, `sqlite`, `lgpd`)
  e conferir se aparece **MIT license**.
- [ ] **Release 1.0.0**: *Releases → Draft a new release*, tag `v1.0.0` na `main`, título
  "1.0.0 — lançamento", com o texto da entrada 1.0.0 do `CHANGELOG.md`. O GitHub gera o
  ZIP que o README manda baixar.

## Conferir depois de abrir

- [ ] Abrir o repositório numa janela anônima do navegador e conferir README, licença e
  `SECURITY.md` (aba *Security → Policy*).
- [ ] Na aba *Security*, conferir que não há alertas abertos (Dependabot e secret
  scanning).
- [x] ~~Gravar o GIF~~: substituído pelo link para o tutorial do site, com capturas de
  tela. O roteiro (`docs/roteiro-gif.md`) ficou como opcional.

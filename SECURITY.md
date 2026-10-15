# Política de segurança

## Para que a app foi feita

A App de Descoberta é uma aplicação **local, para um único usuário**: o consultor a usa
no próprio notebook, e ela escuta só em `127.0.0.1` (o próprio computador). Ela **não tem
login, HTTPS nem controle de acesso**, porque não foi feita para ser acessada por outras
pessoas ou pela rede.

**Não exponha a app à rede** (por exemplo, com `--host 0.0.0.0`, redirecionamento de
porta, túnel ou servidor na nuvem) sem antes aplicar as medidas do guia de uso em
produção (Sprint 9): autenticação, HTTPS, proteção contra CSRF completa, limite de
requisições, criptografia do banco e dos backups, logs de auditoria e teste de intrusão
profissional.

## Versões com correções de segurança

| Versão | Recebe correções |
| --- | --- |
| A mais recente (1.x) | Sim |
| Anteriores | Não: atualize para a mais recente |

## Como relatar uma vulnerabilidade

**Não abra uma issue pública.** Use o relato privado do GitHub:

1. Na página do repositório, abra a aba **Security**.
2. Clique em **Report a vulnerability** (relatar uma vulnerabilidade).
3. Descreva o problema, como reproduzir, a versão (ou o commit) e o impacto que você vê.

O relato fica visível só para o mantenedor. Por favor, não inclua dados pessoais reais
de clientes: use os dados fictícios do banco de demonstração (`uv run --no-dev python -m
descoberta.demo`).

## O que esperar

Este é um projeto pessoal, mantido por uma pessoa, sem prazo garantido. A intenção é:

- confirmar o recebimento em até 7 dias;
- avaliar e responder com um plano (correção, mitigação ou motivo para não corrigir) em
  até 30 dias;
- publicar a correção numa versão nova e registrar o caso no `CHANGELOG.md` e num aviso
  de segurança (GitHub Security Advisory), com crédito a quem relatou, se a pessoa quiser.

## Escopo

**Dentro do escopo** (uso local, como documentado no README):

- leitura ou alteração de dados da app por um site aberto no mesmo navegador (por
  exemplo, DNS rebinding ou CSRF);
- dados pessoais que saem da máquina sem passar pela anonimização e pela prévia
  obrigatória do rascunho por LLM;
- chave de API exposta em log, mensagem de erro, página ou arquivo gerado;
- injeção de conteúdo (HTML, script ou fórmulas) nas páginas ou nos documentos gerados
  (Markdown, DOCX, PDF);
- dependência com vulnerabilidade conhecida que afete a app.

**Fora do escopo:**

- a app exposta à rede, contrariando este documento e o README;
- quem já tem acesso ao computador ou à conta do usuário (pode ler o banco SQLite
  diretamente: proteja o disco com criptografia, veja o README);
- negação de serviço contra a própria máquina do usuário;
- falhas em serviços de terceiros (API da Anthropic, Ollama), que devem ser relatadas a
  eles.

## O que já é verificado automaticamente

A cada mudança, o CI roda as regras de segurança do ruff (flake8-bandit), o `pip-audit`
(dependências com vulnerabilidades conhecidas) e o `gitleaks` (segredos em todo o
histórico do Git); o Dependabot propõe atualizações. Testes automatizados garantem que o
pedido enviado ao LLM não contém os dados pessoais da sessão, que a app recusa outros
endereços além de `127.0.0.1`/`localhost` e que pedidos que gravam dados vindos de outro
site são recusados.

# Revisão de dados pessoais e segredos no histórico do Git

Feita em 14/10/2026, antes de tornar o repositório público (Sprint 8). Escopo: todas as
branches (locais e remotas), todos os commits e o conteúdo do GitHub que também fica
público (descrições, comentários e revisões dos PRs; issues; releases). Este relatório
não reproduz nenhum valor que pudesse ser real.

## Resultado

**Nenhum dado pessoal real e nenhum segredo encontrado.** Não é preciso reescrever o
histórico.

| Verificação | Ferramenta | Resultado |
| --- | --- | --- |
| Segredos em todo o histórico (40 commits com mudanças, todas as branches) | gitleaks 8.30.1 (`gitleaks git --log-opts=--all`) | 1 falso positivo, conferido e liberado no `.gitleaks.toml` (`DESCOBERTA_LLM_PROVEDOR=claude`, nome do provedor) |
| Segredos nos arquivos versionados hoje | gitleaks 8.30.1 (`gitleaks dir` sobre `git archive HEAD`) | nada |
| Detector funcionando | chave falsa no formato da Anthropic, fora do repositório | detectada |
| Arquivos sensíveis já versionados | `git log --all --diff-filter=A` | nenhum `.db`, `.sqlite`, `.env`, chave, `data/` ou `exports/` em nenhum commit |
| Dados pessoais (CPF, CNPJ, e-mail, telefone, CEP, endereço) em cada versão de cada arquivo | `scripts/revisar_historico.py` (o detector da anonimização do LLM) | 651 versões de arquivo de texto lidas; 37 valores distintos, todos fictícios (abaixo) |
| PRs (#1 a #8): descrições, comentários e revisões | `gh pr view` + detector + gitleaks | só o CNPJ de teste do demo |
| Issues e releases | `gh` | nenhum |
| Tags | `git tag` | nenhuma |
| Dependências com vulnerabilidades conhecidas | pip-audit 2.10.1 sobre o `uv.lock` | nenhuma |

## Os 37 valores encontrados pelo detector

Todos são dados de teste, exemplos de formato ou marcadores de lugar, escritos para os
testes da anonimização, do documento fiscal e do perfil, ou para os campos do formulário:

- **Domínios de exemplo** (RFC 2606, `example.com` etc.) e números do demo documentados
  no código (CNPJ de teste 11.222.333/0001-81, CNPJ alfanumérico de exemplo da Receita,
  telefone (11) 90000-0000): 6 valores.
- **CPF e CNPJ de teste**: os números clássicos de exemplo (com dígitos corretos e
  incorretos de propósito), sequências e zeros dos campos do formulário.
- **Telefones**: sequências como 3333-4444 e 98765-4321, em vários formatos, para testar
  o reconhecimento; telefones de "exemplo" com final 0000.
- **Endereços e CEP**: "Rua das Flores, 123", uma avenida e uma rodovia genéricas e o
  CEP do centro de uma cidade, sem pessoa associada.
- **E-mails**: um marcador de lugar (`algo@dominio.tld`) e um e-mail inventado para o
  personagem fictício Roberto, num teste da anonimização.

Os nomes de pessoas e empresas do repositório (Roberto, Marcos, Cida, Construtora
Alvorada, Ana Exemplo, Exemplo Consultoria) são do **caso de referência fictício** da
especificação. **Conferir (Gui):** nenhum deles corresponde a um cliente real.

## Metadados dos commits

- Autor e committer: "Guilherme Ferraz Stauffer", com o e-mail pessoal (43 commits) e o
  e-mail *noreply* do GitHub (8 merges feitos pelo site).
- Decisão (Sprint 8, D3): manter o histórico como está. Ele **não** será reescrito, para
  não mudar os hashes nem quebrar as referências dos PRs. Daqui em diante, os commits usam
  o e-mail *noreply* (como configurar: README, seção "Para desenvolvedores").
- Branches: só nomes de sprint (`sprint-3-persistencia` … `sprint-8-lancamento`,
  `correcao-ci`). Nenhuma tag.

## O que não foi coberto

- **Logs do GitHub Actions** também ficam visíveis num repositório público. Eles contêm
  só a saída do lint e dos testes (com dados fictícios) e nunca usaram segredos (o CI não
  tem nenhum configurado).
- **Bancos e arquivos fora do Git** (`data/`, `.env`, `.venv/`) não são publicados e não
  foram lidos. O gitleaks sobre a pasta inteira acusou itens só em arquivos ignorados pelo
  Git (`.venv/` e, possivelmente, o `.env` local), como era de esperar.

## Como repetir

```bash
uv run python scripts/revisar_historico.py   # dados pessoais em todo o histórico
gitleaks git . --log-opts="--all" --redact   # segredos (também roda no CI: seguranca.yml)
```

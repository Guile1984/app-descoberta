# Atualizar a app

As versões novas saem no GitHub, e as mudanças de cada uma estão no
[CHANGELOG](https://github.com/Guile1984/app-descoberta/blob/main/CHANGELOG.md). Seus dados
ficam na pasta `data`, que você leva da instalação antiga para a nova.

## Passo a passo

1. **Feche a app e faça um backup** do `data\descoberta.db`
   ([como](backup-e-restauracao.md)).
2. **Baixe a versão nova:** no GitHub, **Code → Download ZIP**, e extraia numa **pasta
   nova**. Assim a versão antiga continua lá se precisar voltar.
3. **Copie da pasta antiga para a nova:**
    - a pasta `data`, com o banco (o logotipo fica dentro dele);
    - o `.env`, se você usa o LLM;
    - os arquivos que você criou em `config/` e `prompts/` (por exemplo, um
      `questionario_v2.yaml`). **Não** sobrescreva os arquivos que vieram com a versão
      nova sem comparar: eles podem ter mudado.
4. **Abra pelo `iniciar.bat` da pasta nova.** Na primeira vez, o `uv` baixa as bibliotecas
   novas (precisa de internet).
5. **Confira** os clientes e uma sessão recente.

Quem usa Git pode fazer `git pull` na pasta da app, em vez dos passos 2 e 3.

## O que acontece com o banco

Se a versão nova muda a estrutura do banco (uma coluna ou uma tabela nova), a app
**atualiza o banco sozinha ao abrir**. Isso se chama migração. Ela:

1. faz uma **cópia de segurança** ao lado do banco
   (`data\descoberta.antes-<revisão>-<data>-<hora>.db`), usando a cópia do próprio SQLite,
   que fica íntegra;
2. aplica as mudanças **numa transação só**: se algo der errado no meio, o banco volta a
   como estava;
3. confere no fim que nenhuma referência ficou quebrada.

Num banco já em dia, ela não faz nada, nem a cópia.

**Se a migração falhar**, a app não abre e a janela mostra o motivo. O banco fica como
estava, e a cópia continua lá. Duas mensagens possíveis:

| Mensagem | O que quer dizer |
| --- | --- |
| "a migração falhou e o banco não foi alterado: …" | Um erro no meio da atualização. Nada mudou no banco. Abra a versão antiga (na pasta antiga) e [relate o problema](https://github.com/Guile1984/app-descoberta/issues), sem anexar o banco. |
| "o banco é anterior às migrações, mas o esquema não bate com a versão inicial; nada foi alterado" | O banco é de antes da versão 1.0.0 e foi mudado à mão, ou é de outro programa. A app não arrisca migrar. |

**Bancos de antes da versão 1.0.0** (de antes do Alembic, como um `demo.db` antigo) são
reconhecidos: a app compara a estrutura com a da primeira migração e, se bater, marca o
banco como "versão inicial" e segue, sem perder dados.

## Voltar para a versão anterior

A versão antiga continua na pasta antiga. Mas, se a nova já migrou o banco, a antiga pode
não entender a estrutura nova. Para voltar:

1. feche a app;
2. na pasta **antiga**, coloque como `data\descoberta.db` o seu backup, ou a cópia
   automática `descoberta.antes-…db` feita na migração;
3. abra pelo `iniciar.bat` da pasta antiga.

O que você registrou na versão nova depois da migração não está nessas cópias.

## Para quem desenvolve: criar uma migração

As tabelas ficam em `src/descoberta/repositorio/modelos.py`, e as migrações em
`src/descoberta/repositorio/migracoes/versions/`. Depois de mudar um modelo:

```bash
uv run alembic upgrade head        # leva o banco descartável data/alembic-dev.db à última revisão
uv run alembic revision --autogenerate --rev-id 0002 -m "o que mudou"
```

- A linha de comando do Alembic usa **só** o banco descartável do `alembic.ini`
  (`data/alembic-dev.db`) e ignora `DESCOBERTA_BANCO` de propósito: o banco real é
  migrado apenas pela app, com cópia de segurança antes.
- **Revise o arquivo gerado.** O autogenerate não percebe, por exemplo, a troca do nome de
  uma coluna: ele vê uma coluna apagada e outra criada, o que perderia os dados.
- O ambiente usa o modo "batch" (`render_as_batch=True`), porque o SQLite quase não sabe
  alterar tabelas. Nesse modo, o Alembic cria a tabela nova, copia os dados e troca uma
  pela outra.
- O **teste de deriva** (`tests/repositorio/test_migracoes.py`) falha se os modelos e as
  migrações não derem o mesmo esquema. Ele pega, por exemplo, a migração esquecida.
- Os ids das revisões são números em sequência (`0001`, `0002`…), passados em `--rev-id`.

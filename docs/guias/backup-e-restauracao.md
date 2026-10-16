# Backup e restauração

Tudo o que você registra (clientes, sessões, revisões, relatórios e propostas registrados,
perfil e logotipo) fica num arquivo só: **`data\descoberta.db`**, na pasta da app. São
dados pessoais dos seus clientes, então vale a LGPD: o backup precisa ser tão protegido
quanto o original.

O que **não** está no banco, e também merece cópia se você mudou algo:

- `config/` (o questionário, o modelo da proposta e o `llm.yaml`, se você os adaptou);
- `prompts/`, se você criou prompts novos;
- o `.env`, se você usa o LLM. Ele tem a chave da API: guarde-o como guardaria uma senha.

## Fazer o backup

1. **Feche a app:** feche a janela preta, ou tecle `Ctrl+C` nela. Fechar o navegador não
   basta. Com a app aberta, a cópia pode pegar o banco no meio de uma gravação.
2. **Copie** `data\descoberta.db` para outro lugar, com a data no nome:
   `descoberta-2026-10-16.db`.
3. **Proteja a cópia:** num pendrive ou HD externo **criptografado**, ou compactada com
   senha antes de ir para a nuvem. No [7-Zip](https://www.7-zip.org): formato **7z**,
   criptografia **AES-256** e "Criptografar nomes de arquivos" marcado. Use uma senha
   forte e guarde-a fora do notebook.

**Quando:** depois de cada sessão importante e, no mínimo, uma vez por semana. Guarde mais
de uma cópia (a da semana passada também), para o caso de a mais recente já ter um erro.

??? tip "Pelo PowerShell"
    Na pasta da app, com a app fechada:

    ```powershell
    New-Item -ItemType Directory -Force "$HOME\Documents\backup-descoberta"
    Copy-Item data\descoberta.db "$HOME\Documents\backup-descoberta\descoberta-$(Get-Date -Format yyyy-MM-dd).db"
    ```

    Depois, criptografe a pasta ou o arquivo como acima.

## Restaurar

1. **Feche a app.**
2. **Guarde o banco atual**, por garantia: renomeie `data\descoberta.db` para
   `data\descoberta-antes-de-restaurar.db`.
3. **Coloque a cópia** em `data\descoberta.db` (descompacte antes, se estiver no 7-Zip).
   O nome precisa ser exatamente esse.
4. **Abra a app.** Se a cópia for de uma versão anterior da app, ela atualiza a estrutura
   do banco sozinha ao abrir, guardando antes uma cópia (veja abaixo).
5. Confira os clientes e a última sessão. Se estiver tudo certo, apague o
   `descoberta-antes-de-restaurar.db`.

!!! tip "Restaurar num banco à parte, para conferir"
    Para ver o que há numa cópia sem trocar o seu banco, abra a app apontando para ela:

    ```powershell
    $env:DESCOBERTA_BANCO = "C:\caminho\da\copia.db"
    uv run --no-dev python -m descoberta
    ```

    Feche a janela do terminal ao terminar: a variável vale só nela.

## Cópias automáticas antes de migrar

Quando uma versão nova da app muda a estrutura do banco, ela mesma faz uma cópia **antes**
de mexer nele, ao lado do original:

```text
data\descoberta.antes-0001-20261016-091500.db
```

O nome tem a revisão anterior do banco ("legado" para bancos de antes das migrações) e a
data e a hora. Essas cópias **não substituem o seu backup**: ficam no mesmo disco. Pode
apagá-las depois de conferir que está tudo certo na versão nova. Todos os arquivos `.db`
ficam fora do Git.

## Criptografia do disco

Se o notebook for perdido ou roubado, a criptografia do disco impede que alguém leia o
banco tirando o disco do computador. A app não criptografa o banco por conta própria (veja
[Uso em produção](../explicacao/uso-em-producao.md)).

- **Windows 11 Pro:** ative o **BitLocker** (menu Iniciar → "Gerenciar o BitLocker").
- **Windows 11 Home:** veja se há **Criptografia do dispositivo** em Configurações →
  Privacidade e segurança.
- **Mac:** ative o **FileVault** (Ajustes do Sistema → Privacidade e Segurança).

Guarde a **chave de recuperação** fora do notebook (na sua conta Microsoft ou Apple, ou
impressa num lugar seguro). Sem ela, perder a senha é perder os dados.

## Apagar dados de um cliente

Para atender a um pedido de exclusão (LGPD), use **Excluir** na página do cliente: isso
apaga o cliente, todas as sessões dele e tudo o que pertence a elas (respostas, revisão,
versões registradas, propostas e rascunhos). Lembre que **os backups antigos ainda têm os
dados**: trate-os pela sua política de retenção.

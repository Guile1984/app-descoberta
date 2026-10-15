# Roteiro do GIF de demonstração

GIF curto para o topo do README: mostra, em cerca de 75 segundos, a sessão do caso
Roberto conduzida ao vivo até o relatório. Quem assiste deve entender três coisas: os
cálculos aparecem enquanto o cliente fala, tudo se faz pelo teclado e o relatório sai
pronto.

## Preparação

- **Ferramenta:** [ScreenToGif](https://www.screentogif.com) (grátis, Windows). Grave em
  15 quadros por segundo.
- **Tela:** janela do navegador com **1280 × 720**, zoom em 100%, sem favoritos nem outras
  abas visíveis. Feche notificações (Windows: "Não incomodar" ligado).
- **Dados:** só o banco de demonstração, que é fictício. Antes de gravar:

  ```powershell
  uv run --no-dev python -m descoberta.demo
  $env:DESCOBERTA_BANCO = "data/demo.db"
  uv run --no-dev python -m descoberta
  ```

- Para a parte "ao vivo" ter o que preencher, abra a sessão do Roberto e **apague** antes
  as respostas da cena 3 e o investimento (bloco 9), para digitá-los durante a gravação.
- Ensaie uma vez sem gravar; digite num ritmo calmo (o GIF pode ser acelerado depois).

## Cenas

| # | Duração | O que fazer | O que aparece |
| --- | --- | --- | --- |
| 1 | 5 s | Tela inicial com a lista de clientes; clique em **Construtora Alvorada** e na sessão | O cliente e a sessão do caso Roberto |
| 2 | 8 s | Tecle `Ctrl+/`, espere 2 s, `Esc` | A ajuda com os atalhos de teclado |
| 3 | 15 s | `Alt+1`; digite uma resposta curta na primeira pergunta; `Tab`; digite "4" (horas) e "15" (chamados) | O aviso "Salvo às…" e o painel de cálculos mostrando 60 h/mês |
| 4 | 8 s | `Alt+S` e `Espaço` num sinal de alerta; `Alt+N`, digite "Validar com o Marcos" e `Ctrl+Enter` | O sinal marcado e a anotação na lista |
| 5 | 12 s | `Alt+9`; vá ao investimento e digite "20.000"; `Tab`; `Alt+C` | O payback de ~7,7 meses e o score final 12 → **Seguir com fase 0** |
| 6 | 10 s | Clique em **Revisão pós-sessão →**; role devagar até a matriz de riscos | A matriz 3×3 e "Nada falta nas saídas da revisão" |
| 7 | 12 s | Clique em **Relatório →**; role pela prévia; clique em **Registrar versão enviada** | A prévia do relatório e a versão 1 registrada, com o hash |
| 8 | 5 s | Clique em **PDF** na versão registrada e abra o arquivo | O PDF com o rodapé (versão, data e hash) |

Total: cerca de 75 segundos.

## Acabamento

- No editor do ScreenToGif: corte as esperas, acelere a digitação (até 1,5×) e mantenha
  cada resultado importante parado por 2 s (cenas 3, 5 e 7).
- Exporte em GIF com **no máximo 8 MB** (o GitHub mostra GIFs grandes, mas carregam
  devagar). Se passar disso: reduza para 12 quadros por segundo ou recorte a área.
- Salve em `docs/img/demo.gif` e, no README, troque a linha "Demonstração em vídeo: em
  breve" pela imagem que está no comentário logo acima dela.
- Confira o GIF quadro a quadro: só podem aparecer os dados fictícios do demo (Roberto,
  Construtora Alvorada, Ana Exemplo), nunca um cliente real, uma notificação ou outra aba.

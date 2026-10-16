# Atalhos de teclado

Valem na **tela da sessão**, a página onde você conduz a conversa. Na própria app, tecle
`Ctrl+/` para ver esta lista.

| Teclas | O que faz |
| --- | --- |
| `Ctrl+/ ou ?` | Abre e fecha a ajuda dos atalhos. O `?` só vale com o cursor fora de um campo de texto (dentro de um campo, ele é só o caractere digitado). |
| `Alt+1 … Alt+9, Alt+0` | Vai para o bloco 1 a 9; `Alt+0` vai para o bloco 10. |
| `Alt+R` | Vai para a aba do encerramento. |
| `Alt+P` | Vai para a próxima pergunta obrigatória sem resposta. Quando acabam as do bloco, abre o próximo bloco que ainda tem pendências (depois do último, volta ao primeiro); sem nenhuma pendência, vai para o indicador de obrigatórias. |
| `Alt+S` | Vai para os sinais de alerta do bloco: `Tab` passa de um sinal ao outro e `Espaço` marca ou desmarca. |
| `Alt+N` | Põe o cursor na caixa de anotação. |
| `Ctrl+Enter` | Com o cursor na caixa de anotação: salva a anotação e volta ao campo onde você estava. |
| `Alt+C` | Vai para o painel de cálculos. |
| `Alt+T` | Inicia, pausa ou retoma o cronômetro da sessão. |
| `Esc` | Volta ao último campo de resposta em que você estava. Com a ajuda aberta, fecha a ajuda. |

## Detalhes

- **Os atalhos de bloco usam a tecla física.** `Alt+1` funciona igual em qualquer layout de
  teclado, inclusive o ABNT2. Já o `Ctrl+/` e o `?` dependem do caractere que a tecla
  digita, e por isso funcionam onde o `/` e o `?` estiverem no seu teclado.
- **Por que não `Alt+D`, `Alt+E` ou `Alt+F`:** o Chrome e o Edge já usam essas teclas (barra
  de endereço e menus).
- **Uma lista só.** A tabela da ajuda e o que cada tecla faz saem da mesma lista no código
  (`src/descoberta/web/atalhos.py`), que o arquivo `src/descoberta/web/static/atalhos.js`
  lê. Assim a ajuda nunca mostra um atalho diferente do que funciona, e um teste confere que
  esta página também lista todos.
- **Salvar não tem atalho:** cada campo salva sozinho quando você para de digitar ou sai
  dele (veja [Conduzir uma sessão ao vivo](../guias/sessao-ao-vivo.md)).
